"""
================================================================================
PROJE ADI   : BÜYÜK TARAMA VE SKORLAMA ROBOTU (ULTIMATE SCORER)
YAZAR       : Borsa (AI Assistant)
VERSIYON    : 3.1 (CSV Çıktılı)

MANTIK:
A. BALINA GÜCÜ (%40): En iyi alıcı toplam hacmin %20'sini almış mı? Maliyeti fiyata yakın mı?
B. TREND (%30): Fiyat ortalamanın üstünde mi? Para girişi var mı?
C. NİYET (%20): Bekleyen emirlerde alıcı istekli mi? Fiyat Pivot üstü mü?
D. DERİNLİK (%10): Alış kademeleri satıştan dolu mu?

ÇIKTI:
0-100 Arası Skor ve Net Sinyal Tablosu (CSV formatında)
================================================================================
"""

import pandas as pd
import os
from datetime import datetime

# --- AYARLAR ---
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün"  # CSV dosyalarının okunacağı konum
CIKTI_KONUMU = r"C:\Kullanıcılar\RaporKlasörün"  # CSV raporlarının kaydedileceği konum

def buyuk_tarama_robotu(ana_dizin):
    print(f"[{ana_dizin}] üzerinde Büyük Tarama Robotu çalışıyor...")
    
    # Dosya Yolları
    yol_maliyet = os.path.join(ana_dizin, 'MALIYET_ALICI-1.csv')
    yol_kademe = os.path.join(ana_dizin, 'KADEME_ANALIZI.csv')
    yol_bekleyen = os.path.join(ana_dizin, 'BEKLEYEN_EMIRLER.csv')
    yol_fiyat = os.path.join(ana_dizin, 'ACILISLAR-1.csv')
    yol_alis = os.path.join(ana_dizin, 'DERINLIK_ALIS-1.csv')
    yol_satis = os.path.join(ana_dizin, 'DERINLIK_SATIS-1.csv')
    
    try:
        # --- VERİLERİ OKU ---
        # 1. Maliyet Verisi (Balina)
        df_maliyet = pd.read_csv(yol_maliyet)[['SEMBOL', 'ENIYI ALICI.1', 'NET ADET', 'MALIYET']]
        df_maliyet.rename(columns={'ENIYI ALICI.1': 'BALINA_ADI', 'NET ADET': 'BALINA_LOT', 'MALIYET': 'BALINA_MALIYET'}, inplace=True)
        
        # 2. Kademe Verisi (Trend)
        df_kademe = pd.read_csv(yol_kademe)[['SEMBOL', 'TOPLAM', 'AORT', 'ALIS', 'SATIS']]
        df_kademe.rename(columns={'TOPLAM': 'TOPLAM_ISLEM_LOT', 'ALIS': 'AKTIF_ALIS', 'SATIS': 'AKTIF_SATIS'}, inplace=True)
        
        # 3. Fiyat Verisi (Kapanış & Pivot)
        df_fiyat = pd.read_csv(yol_fiyat)[['SEMBOL', 'KAPANIS', 'YUKSEK', 'DUSUK']]
        # Pivot Hesabı: (Yüksek + Düşük + Kapanış) / 3
        df_fiyat['PIVOT'] = (df_fiyat['YUKSEK'] + df_fiyat['DUSUK'] + df_fiyat['KAPANIS']) / 3
        
        # 4. Bekleyen Emir (Teorik Niyet Simülasyonu)
        df_bekleyen = pd.read_csv(yol_bekleyen)[['SEMBOL', 'NET.EMIR.FARKI']]
        
        # 5. Derinlik Verisi (Destek)
        # Derinlik dosyalarını oku ve toplam lotları hesapla (Satır bazlı)
        df_d_alis = pd.read_csv(yol_alis)
        df_d_satis = pd.read_csv(yol_satis)
        
        # Alış toplamı
        alis_cols = [c for c in df_d_alis.columns if 'ADET' in c]
        df_d_alis['TOPLAM_DERINLIK_ALIS'] = df_d_alis[alis_cols].sum(axis=1)
        
        # Satış toplamı
        satis_cols = [c for c in df_d_satis.columns if 'ADET' in c]
        df_d_satis['TOPLAM_DERINLIK_SATIS'] = df_d_satis[satis_cols].sum(axis=1)
        
        # --- BİRLEŞTİRME (MERGE) ---
        df = pd.merge(df_maliyet, df_kademe, on='SEMBOL', how='inner')
        df = pd.merge(df, df_fiyat, on='SEMBOL', how='inner')
        df = pd.merge(df, df_bekleyen, on='SEMBOL', how='left')
        df = pd.merge(df, df_d_alis[['SEMBOL', 'TOPLAM_DERINLIK_ALIS']], on='SEMBOL', how='left')
        df = pd.merge(df, df_d_satis[['SEMBOL', 'TOPLAM_DERINLIK_SATIS']], on='SEMBOL', how='left')
        
        # --- PUANLAMA MOTORU ---
        
        sonuclar = []
        for index, row in df.iterrows():
            puan = 0
            analiz_detay = []
            
            # --- A. BALINA GÜCÜ (40 PUAN) ---
            # Kural 1: En iyi alıcı net adet > Toplam Hacim * 0.20 (+20 Puan)
            balina_gucu = False
            if row['BALINA_LOT'] > (row['TOPLAM_ISLEM_LOT'] * 0.20):
                puan += 20
                balina_gucu = True
            
            # Kural 2: Balina Maliyeti Fiyat Farkı %-2 ile %2 arasındaysa (+20 Puan)
            fark_yuzde = ((row['KAPANIS'] - row['BALINA_MALIYET']) / row['BALINA_MALIYET']) * 100
            maliyet_uygun = False
            if -2 <= fark_yuzde <= 2:
                puan += 20
                maliyet_uygun = True
            
            # --- B. TREND VE KADEME (30 PUAN) ---
            # Kural 1: Anlık Fiyat > AORT (+15 Puan)
            trend_pozitif = False
            if row['KAPANIS'] > row['AORT']:
                puan += 15
                trend_pozitif = True
                
            # Kural 2: Alış Lot > Satış Lot (Para Girişi) (+15 Puan)
            para_girisi = False
            if row['AKTIF_ALIS'] > row['AKTIF_SATIS']:
                puan += 15
                para_girisi = True
                
            # --- C. TEORİK NİYET / PIVOT (20 PUAN) ---
            # Kural 1: Bekleyen Net Emir > 0 (Alıcılı) (+10 Puan)
            niyet_alicili = False
            if row['NET.EMIR.FARKI'] > 0:
                puan += 10
                niyet_alicili = True
                
            # Kural 2: Fiyat > Pivot (+10 Puan)
            pivot_ustu = False
            if row['KAPANIS'] > row['PIVOT']:
                puan += 10
                pivot_ustu = True
                
            # --- D. DERİNLİK DESTEĞİ (10 PUAN) ---
            # Kural 1: Toplam Alış Derinlik > Toplam Satış Derinlik (+10 Puan)
            derinlik_saglam = False
            if row['TOPLAM_DERINLIK_ALIS'] > row['TOPLAM_DERINLIK_SATIS']:
                puan += 10
                derinlik_saglam = True
                
            # --- SİNYAL OLUŞTURMA ---
            sinyal = "NÖTR"
            if puan >= 80: sinyal = "🚀 MEGA BOĞA"
            elif puan >= 60: sinyal = "🟢 GÜÇLÜ AL"
            elif puan >= 40: sinyal = "🟡 İZLE"
            else: sinyal = "🔴 SAT / NEGATİF"
            
            # Tablo İçin Durum Metinleri
            balina_durumu = f"TOPLUYOR ({str(row['BALINA_ADI']).strip()})" if balina_gucu else "ZAYIF"
            trend_durumu = "POZİTİF" if trend_pozitif and para_girisi else ("KARIŞIK" if trend_pozitif or para_girisi else "NEGATİF")
            teorik_durumu = "ALICILI" if niyet_alicili else "SATICILI"

            sonuclar.append({
                'SEMBOL': row['SEMBOL'],
                'SKOR': int(puan),
                'SİNYAL': sinyal,
                'BALINA_DURUMU': balina_durumu,
                'TREND': trend_durumu,
                'TEORİK': teorik_durumu,
                'FİYAT': row['KAPANIS'],
                'BALINA_MLYT': round(row['BALINA_MALIYET'], 2)
            })
            
        return pd.DataFrame(sonuclar)

    except Exception as e:
        print(f"HATA: {e}")
        return None

# --- ROBOTU ÇALIŞTIR ---
df_sonuc = buyuk_tarama_robotu(DOSYA_KONUMU)

if df_sonuc is not None:
    # Çıktı klasörünü kontrol et ve yoksa oluştur
    if not os.path.exists(CIKTI_KONUMU):
        os.makedirs(CIKTI_KONUMU)
        print(f"✓ Çıktı klasörü oluşturuldu: {CIKTI_KONUMU}")
    
    # Zaman damgası
    zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Skor'a göre sırala (En yüksek en üstte)
    df_sirali = df_sonuc.sort_values(by='SKOR', ascending=False)
    
    print("\n" + "="*95)
    print(" GÜNLÜK BÜYÜK TARAMA RAPORU (BALINA + TREND + NİYET + DERİNLİK)")
    print("="*95)
    
    # İlk 20 Hisseyi Göster
    cols = ['SEMBOL', 'SKOR', 'SİNYAL', 'BALINA_DURUMU', 'TREND', 'TEORİK', 'FİYAT', 'BALINA_MLYT']
    print(df_sirali[cols].head(20).to_string(index=False))
    
    # En Kötüleri Göster (Short Adayları)
    print("\n" + "="*95)
    print(" EN DÜŞÜK SKORLU HİSSELER (SATIŞ BASKISI)")
    print("="*95)
    print(df_sirali[cols].tail(10).to_string(index=False))
    
    # CSV olarak kaydet
    # 1. Tüm Tarama Sonuçları
    tum_dosya = os.path.join(CIKTI_KONUMU, f'BUYUK_TARAMA_TUM_{zaman_damgasi}.csv')
    df_sirali.to_csv(tum_dosya, index=False, encoding='utf-8-sig')
    print(f"\n✓ Tüm tarama sonuçları: {tum_dosya}")
    
    # 2. En İyi 20 (Yüksek Skor)
    en_iyi_dosya = os.path.join(CIKTI_KONUMU, f'BUYUK_TARAMA_EN_IYI_{zaman_damgasi}.csv')
    df_sirali.head(20).to_csv(en_iyi_dosya, index=False, encoding='utf-8-sig')
    print(f"✓ En iyi 20 hisse: {en_iyi_dosya}")
    
    # 3. En Kötü 10 (Short Adayları)
    en_kotu_dosya = os.path.join(CIKTI_KONUMU, f'BUYUK_TARAMA_SHORT_ADAY_{zaman_damgasi}.csv')
    df_sirali.tail(10).to_csv(en_kotu_dosya, index=False, encoding='utf-8-sig')
    print(f"✓ Short adayları: {en_kotu_dosya}")
    
    print("\n" + "="*95)
    print(" ANALİZ TAMAMLANDI - TÜM RAPORLAR CSV OLARAK KAYDEDİLDİ")
    print("="*95)