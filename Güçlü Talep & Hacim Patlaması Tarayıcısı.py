"""
================================================================================
PROJE ADI   : Güçlü Talep & Hacim Patlaması Tarayıcısı
YAZAR       : Borsa (AI Assistant)
VERSIYON    : 1.3 (CSV Çıktılı)

AÇIKLAMA:
Bu script, fiyat yükselişini hacim ve aktif alıcı desteğiyle teyit eder.
Sadece fiyatı artan değil, "içerisine para giren" hisseleri bulur.

KRİTERLER:
1. Rölatif Hacim > 1.5 (Bugünkü hacim, son 5 gün ortalamasının en az %50 üzerinde)
2. Fiyat Değişimi > %2 (Hisse günü en az %2 primli geçiriyor)
3. Aktif Denge > 0 (Alıcılar satıcılardan daha istekli - Para Girişi Var)
================================================================================
"""

import pandas as pd
import os
from datetime import datetime

# --- AYARLAR ---
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün"  # CSV dosyalarının okunacağı konum
CIKTI_KONUMU = r"C:\Kullanıcılar\RaporKlasörün"  # CSV raporlarının kaydedileceği konum

def guclu_talep_analizi(ana_dizin):
    print(f"[{ana_dizin}] klasöründeki verilerle talep analizi yapılıyor...")
    
    yol_fiyat = os.path.join(ana_dizin, 'ACILISLAR-1.csv')
    yol_kademe = os.path.join(ana_dizin, 'KADEME_ANALIZI.csv')
    
    try:
        # 1. Dosyaları Oku
        df_fiyat = pd.read_csv(yol_fiyat)
        df_kademe = pd.read_csv(yol_kademe)
        
        # 2. Hacim Ortalamasını Hesapla (Son 5 Gün)
        # Sütunlar: HACIM-1, HACIM-2 ... HACIM-5
        hacim_cols = [f'HACIM-{i}' for i in range(1, 6)]
        
        # Eğer bu sütunlar varsa ortalama al
        if all(col in df_fiyat.columns for col in hacim_cols):
            df_fiyat['ORT_HACIM_5G'] = df_fiyat[hacim_cols].mean(axis=1)
            
            # Rölatif Hacim (Bugün / Ortalama)
            # 1.0 = Ortalama kadar, 2.0 = Ortalamanın 2 katı
            df_fiyat['ROLATIF_HACIM'] = df_fiyat['HACIM'] / df_fiyat['ORT_HACIM_5G']
            
            # Fiyat Değişimi (%)
            # ((Kapanış - Önceki Kapanış) / Önceki Kapanış) * 100
            df_fiyat['DEGISIM_YUZDE'] = ((df_fiyat['KAPANIS'] - df_fiyat['KAPANIS-1']) / df_fiyat['KAPANIS-1']) * 100
        else:
            print("HATA: Hacim geçmiş verileri (HACIM-1, HACIM-2 vb.) bulunamadı.")
            return None

        # 3. Kademeleri Hazırla
        # Sadece SEMBOL ve FARK (Net Para Girişi) lazım
        df_kademe_kisa = df_kademe[['SEMBOL', 'FARK']].rename(columns={'FARK': 'NET_PARA_GIRIS_LOT'})
        
        # 4. Verileri Birleştir
        df_merged = pd.merge(df_fiyat, df_kademe_kisa, on='SEMBOL', how='inner')
        
        return df_merged

    except FileNotFoundError:
        print("HATA: Dosya bulunamadı.")
        return None
    except Exception as e:
        print(f"HATA: {e}")
        return None

# --- ANALİZİ BAŞLAT ---
df_analiz = guclu_talep_analizi(DOSYA_KONUMU)

if df_analiz is not None:
    # Çıktı klasörünü kontrol et ve yoksa oluştur
    if not os.path.exists(CIKTI_KONUMU):
        os.makedirs(CIKTI_KONUMU)
        print(f"✓ Çıktı klasörü oluşturuldu: {CIKTI_KONUMU}")
    
    # Zaman damgası
    zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # --- FİLTRELEME KURALLARI ---
    # 1. Hacim patlaması olsun (Ortalamanın 1.5 katı)
    # 2. Hisse yükseliyor olsun (>%2)
    # 3. Gerçekten alıcı girmiş olsun (Net Para Girişi > 0)
    
    guclu_talep = df_analiz[
        (df_analiz['ROLATIF_HACIM'] > 1.5) &
        (df_analiz['DEGISIM_YUZDE'] > 2.0) &
        (df_analiz['NET_PARA_GIRIS_LOT'] > 0)
    ].sort_values(by='ROLATIF_HACIM', ascending=False)
    
    # Sonuçları Göster
    cols_to_show = ['SEMBOL', 'KAPANIS', 'DEGISIM_YUZDE', 'ROLATIF_HACIM', 'NET_PARA_GIRIS_LOT']
    
    print("\n" + "="*75)
    print(" GÜÇLÜ TALEP GÖREN HİSSELER (HACIM + FİYAT + PARA GİRİŞİ)")
    print("="*75)
    
    # Okunabilirlik için sayı formatlama
    pd.options.display.float_format = '{:,.2f}'.format
    print(guclu_talep[cols_to_show].head(15).to_string(index=False))
    
    # CSV olarak kaydet
    guclu_talep_dosya = os.path.join(CIKTI_KONUMU, f'GUCLU_TALEP_{zaman_damgasi}.csv')
    guclu_talep.to_csv(guclu_talep_dosya, index=False, encoding='utf-8-sig')
    print(f"\n✓ Güçlü talep raporu: {guclu_talep_dosya}")
    
    print("\n[YORUM]: 'ROLATIF_HACIM' 2.0 ise, hisse normalden 2 kat fazla işlem görüyor demektir.")
    
    print("\n" + "="*75)
    print(" ANALİZ TAMAMLANDI - RAPOR CSV OLARAK KAYDEDİLDİ")
    print("="*75)