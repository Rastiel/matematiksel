"""
================================================================================
PROJE ADI   : Spread (Makas) ve Volatilite Analizi
YAZAR       : Borsa (AI Assistant)
VERSIYON    : 1.1 (CSV Çıktılı)

AÇIKLAMA:
Bu script, hisselerin Alış-Satış makasını (Spread) hesaplar.
Makasın dar olması likiditenin yüksek olduğunu ve olası bir kırılımı işaret eder.
Makasın açık olması ise riskin yüksek olduğunu gösterir.

ÇIKTI:
- SPREAD_YUZDE: (Satış - Alış) / Alış
- GUN_ICI_MARJ: (Yüksek - Düşük) / Düşük
================================================================================
"""

import pandas as pd
import os
from datetime import datetime

# --- AYARLAR ---
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün"  # CSV dosyalarının okunacağı konum
CIKTI_KONUMU = r"C:\Kullanıcılar\RaporKlasörün"  # CSV raporlarının kaydedileceği konum

def spread_analizi(ana_dizin):
    print(f"[{ana_dizin}] klasöründeki verilerle Spread analizi yapılıyor...")
    
    yol_alis = os.path.join(ana_dizin, 'DERINLIK_ALIS-1.csv')
    yol_satis = os.path.join(ana_dizin, 'DERINLIK_SATIS-1.csv')
    yol_fiyat = os.path.join(ana_dizin, 'ACILISLAR-1.csv')
    
    try:
        # 1. Verileri Oku (Sadece en iyi fiyatlar yeterli)
        df_alis = pd.read_csv(yol_alis)[['SEMBOL', '1 ALIS']]
        df_satis = pd.read_csv(yol_satis)[['SEMBOL', '1 SATIS']]
        
        # Fiyat verisi (Gün içi marj için)
        if os.path.exists(yol_fiyat):
            df_fiyat = pd.read_csv(yol_fiyat)[['SEMBOL', 'YUKSEK', 'DUSUK', 'KAPANIS']]
        else:
            df_fiyat = pd.DataFrame(columns=['SEMBOL', 'YUKSEK', 'DUSUK', 'KAPANIS'])
        
        # 2. Birleştir
        df = pd.merge(df_alis, df_satis, on='SEMBOL', how='inner')
        df = pd.merge(df, df_fiyat, on='SEMBOL', how='left')
        
        # 3. Hesaplamalar
        # Spread (Makas) Hesabı
        df['SPREAD_TL'] = df['1 SATIS'] - df['1 ALIS']
        df['SPREAD_YUZDE'] = (df['SPREAD_TL'] / df['1 ALIS']) * 100
        
        # Gün İçi Volatilite (Range) Hesabı
        if 'YUKSEK' in df.columns:
            df['GUN_ICI_MARJ_YUZDE'] = ((df['YUKSEK'] - df['DUSUK']) / df['DUSUK']) * 100
        else:
            df['GUN_ICI_MARJ_YUZDE'] = 0
            
        return df

    except Exception as e:
        print(f"HATA: {e}")
        return None

# --- ANALİZİ BAŞLAT ---
df_spread = spread_analizi(DOSYA_KONUMU)

if df_spread is not None:
    # Çıktı klasörünü kontrol et ve yoksa oluştur
    if not os.path.exists(CIKTI_KONUMU):
        os.makedirs(CIKTI_KONUMU)
        print(f"✓ Çıktı klasörü oluşturuldu: {CIKTI_KONUMU}")
    
    # Zaman damgası
    zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. SIKIŞANLAR (SPREAD DARALMASI) - Fırsat Adayları
    # Spread %0.5'in altında olanlar (Çok likit)
    sikisanlar = df_spread[
        (df_spread['SPREAD_YUZDE'] < 0.5) & 
        (df_spread['SPREAD_YUZDE'] > 0) 
    ].sort_values(by='SPREAD_YUZDE', ascending=True).head(15)
    
    print("\n" + "="*85)
    print(" MAKASI EN DAR HİSSELER (HAREKET HAZIRLIĞI / YÜKSEK LİKİDİTE)")
    print("="*85)
    print(sikisanlar[['SEMBOL', '1 ALIS', '1 SATIS', 'SPREAD_YUZDE', 'GUN_ICI_MARJ_YUZDE']].to_string(index=False))
    
    # CSV olarak kaydet
    # 1. Tüm Spread Analizi
    tum_dosya = os.path.join(CIKTI_KONUMU, f'SPREAD_ANALIZI_TUM_{zaman_damgasi}.csv')
    df_spread.sort_values(by='SPREAD_YUZDE', ascending=True).to_csv(tum_dosya, index=False, encoding='utf-8-sig')
    print(f"\n✓ Tüm spread analizi: {tum_dosya}")
    
    # 2. Dar Makaslı (Likit)
    dar_dosya = os.path.join(CIKTI_KONUMU, f'SPREAD_ANALIZI_DAR_MAKAS_{zaman_damgasi}.csv')
    sikisanlar.to_csv(dar_dosya, index=False, encoding='utf-8-sig')
    print(f"✓ Dar makaslı hisseler: {dar_dosya}")
    
    print("\n[YORUM]: Bu hisselerde 'SPREAD_YUZDE' çok düşük olduğu için kademeler arası geçiş hızlıdır.")
    print("Gün içi trade (al-sat) için en uygun hisseler bunlardır.")
    
    print("\n" + "="*85)
    print(" ANALİZ TAMAMLANDI - RAPORLAR CSV OLARAK KAYDEDİLDİ")
    print("="*85)