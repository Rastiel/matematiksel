"""
================================================================================
PROJE ADI   : WAPD - Ağırlıklı Ortalama Derinlik Analizi
YAZAR       : Borsa (AI Assistant)
VERSIYON    : 1.1 (CSV Çıktılı)

AÇIKLAMA:
Bu script, 'Weighted Average Price Depth' (WAPD) hesaplar.
Basitçe; tahtadaki tüm alıcıların ve satıcıların "Ağırlık Merkezini" bulur.

STRATEJİ:
- Eğer Alış WAPD, Güncel Fiyata çok yakınsa -> GÜÇLÜ DESTEK.
- Eğer Satış WAPD, Güncel Fiyata çok yakınsa -> GÜÇLÜ DİRENÇ / BASKI.
================================================================================
"""

import pandas as pd
import os
from datetime import datetime

# --- AYARLAR ---
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün"  # CSV dosyalarının okunacağı konum
CIKTI_KONUMU = r"C:\Kullanıcılar\RaporKlasörün"  # CSV raporlarının kaydedileceği konum
KADEME_DERINLIGI = 14

def wapd_analizi(ana_dizin, derinlik_siniri):
    print(f"[{ana_dizin}] klasöründeki verilerle WAPD hesaplanıyor...")
    
    yol_alis = os.path.join(ana_dizin, 'DERINLIK_ALIS-1.csv')
    yol_satis = os.path.join(ana_dizin, 'DERINLIK_SATIS-1.csv')
    yol_fiyat = os.path.join(ana_dizin, 'ACILISLAR-1.csv')
    
    try:
        df_alis = pd.read_csv(yol_alis)
        df_satis = pd.read_csv(yol_satis)
        # Fiyat dosyasını sadece referans (Kapanış) için alıyoruz
        if os.path.exists(yol_fiyat):
            df_fiyat = pd.read_csv(yol_fiyat)[['SEMBOL', 'KAPANIS']]
        else:
            print("UYARI: Fiyat dosyası bulunamadı, uzaklık analizi yapılamayacak.")
            df_fiyat = pd.DataFrame(columns=['SEMBOL', 'KAPANIS'])
        
        # Verileri Birleştir
        df = pd.merge(df_alis, df_satis, on='SEMBOL', how='inner', suffixes=('_ALIS', '_SATIS'))
        df = pd.merge(df, df_fiyat, on='SEMBOL', how='left')
        
        sonuclar = []

        for index, row in df.iterrows():
            sembol = row['SEMBOL']
            kapanis = row['KAPANIS']
            
            # --- WAPD (ALIŞ) HESABI ---
            # Formül: Toplam (Fiyat * Lot) / Toplam Lot
            toplam_hacim_alis = 0 
            toplam_lot_alis = 0
            
            for i in range(1, derinlik_siniri + 1):
                col_adet = f"{i} ALIS ADET"
                col_fiyat = f"{i} ALIS"
                if col_adet in row and col_fiyat in row:
                    adet = row[col_adet]
                    fiyat = row[col_fiyat]
                    if pd.notna(adet) and pd.notna(fiyat):
                        toplam_hacim_alis += (adet * fiyat)
                        toplam_lot_alis += adet
            
            wapd_alis = toplam_hacim_alis / toplam_lot_alis if toplam_lot_alis > 0 else 0

            # --- WAPD (SATIŞ) HESABI ---
            toplam_hacim_satis = 0
            toplam_lot_satis = 0
            
            for i in range(1, derinlik_siniri + 1):
                col_adet = f"{i} SATIS ADET"
                col_fiyat = f"{i} SATIS"
                if col_adet in row and col_fiyat in row:
                    adet = row[col_adet]
                    fiyat = row[col_fiyat]
                    if pd.notna(adet) and pd.notna(fiyat):
                        toplam_hacim_satis += (adet * fiyat)
                        toplam_lot_satis += adet

            wapd_satis = toplam_hacim_satis / toplam_lot_satis if toplam_lot_satis > 0 else 0
            
            # --- ANALİZ ---
            # WAPD'nin şu anki fiyata uzaklığı (%)
            destek_uzaklik = ((kapanis - wapd_alis) / kapanis * 100) if pd.notna(kapanis) and wapd_alis else 999
            direnc_uzaklik = ((wapd_satis - kapanis) / kapanis * 100) if pd.notna(kapanis) and wapd_satis else 999
            
            sonuclar.append({
                'SEMBOL': sembol,
                'KAPANIS': kapanis,
                'WAPD_ALIS': wapd_alis,
                'WAPD_SATIS': wapd_satis,
                'DESTEK_UZAKLIK_YUZDE': destek_uzaklik,
                'DIRENC_UZAKLIK_YUZDE': direnc_uzaklik,
                'TOPLAM_ALIS_LOT': int(toplam_lot_alis),
                'TOPLAM_SATIS_LOT': int(toplam_lot_satis)
            })
            
        return pd.DataFrame(sonuclar)

    except Exception as e:
        print(f"HATA: {e}")
        return None

# --- RAPORLAMA ---
df_wapd = wapd_analizi(DOSYA_KONUMU, KADEME_DERINLIGI)

if df_wapd is not None:
    # Çıktı klasörünü kontrol et ve yoksa oluştur
    if not os.path.exists(CIKTI_KONUMU):
        os.makedirs(CIKTI_KONUMU)
        print(f"✓ Çıktı klasörü oluşturuldu: {CIKTI_KONUMU}")
    
    # Zaman damgası
    zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. GÜVENLİ LİMANLAR (Alış Desteği Yakın ve Güçlü)
    guvenli = df_wapd[
        (df_wapd['DESTEK_UZAKLIK_YUZDE'] < 2.0) &  # %2'den daha yakın destek
        (df_wapd['DESTEK_UZAKLIK_YUZDE'] > -5.0) & # Çok da yukarıda olmasın (anomali)
        (df_wapd['TOPLAM_ALIS_LOT'] > df_wapd['TOPLAM_SATIS_LOT']) # Alıcılar baskın
    ].sort_values(by='DESTEK_UZAKLIK_YUZDE', ascending=True)
    
    print("\n" + "="*85)
    print(" GÜVENLİ LİMANLAR (WAPD DESTEĞİ FİYATA ÇOK YAKIN)")
    print("="*85)
    print(guvenli[['SEMBOL', 'KAPANIS', 'WAPD_ALIS', 'DESTEK_UZAKLIK_YUZDE']].head(10).to_string(index=False))

    # 2. RİSKLİ BÖLGE (Satış Direnci Yakın ve Baskın)
    riskli = df_wapd[
        (df_wapd['DIRENC_UZAKLIK_YUZDE'] < 2.0) & # %2'den daha yakın direnç
        (df_wapd['TOPLAM_SATIS_LOT'] > df_wapd['TOPLAM_ALIS_LOT']) # Satıcılar baskın
    ].sort_values(by='DIRENC_UZAKLIK_YUZDE', ascending=True)

    print("\n" + "="*85)
    print(" SATIŞ BASKISI ALTINDAKİLER (WAPD DİRENCİ FİYATA ÇOK YAKIN)")
    print("="*85)
    print(riskli[['SEMBOL', 'KAPANIS', 'WAPD_SATIS', 'DIRENC_UZAKLIK_YUZDE']].head(10).to_string(index=False))
    
    # CSV olarak kaydet
    # 1. Tüm WAPD Analizi
    tum_dosya = os.path.join(CIKTI_KONUMU, f'WAPD_ANALIZI_TUM_{zaman_damgasi}.csv')
    df_wapd.to_csv(tum_dosya, index=False, encoding='utf-8-sig')
    print(f"\n✓ Tüm WAPD analizi: {tum_dosya}")
    
    # 2. Güvenli Limanlar
    guvenli_dosya = os.path.join(CIKTI_KONUMU, f'WAPD_ANALIZI_GUVENLI_{zaman_damgasi}.csv')
    guvenli.to_csv(guvenli_dosya, index=False, encoding='utf-8-sig')
    print(f"✓ Güvenli limanlar: {guvenli_dosya}")
    
    # 3. Riskli Bölge
    riskli_dosya = os.path.join(CIKTI_KONUMU, f'WAPD_ANALIZI_RISKLI_{zaman_damgasi}.csv')
    riskli.to_csv(riskli_dosya, index=False, encoding='utf-8-sig')
    print(f"✓ Riskli bölge: {riskli_dosya}")
    
    print("\n" + "="*85)
    print(" ANALİZ TAMAMLANDI - RAPORLAR CSV OLARAK KAYDEDİLDİ")
    print("="*85)