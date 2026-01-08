"""
================================================================================
PROJE ADI   : Sıkışma Alanı (Squeeze) Tespit Robotu
YAZAR       : Borsa (AI Assistant)
VERSIYON    : 1.1 (CSV Çıktılı)

AÇIKLAMA:
Bu script, hisselerin son 11 günlük fiyat hareketlerini analiz eder.
Fiyatın çok dar bir banda sıkıştığı (Volatilitenin düştüğü) hisseleri tespit eder.
Bu hisseler genellikle sert bir kırılım (yukarı veya aşağı) yaşamaya adaydır.

VERİ KAYNAĞI:
- ACILISLAR-1.csv (Güncel ve yakın geçmiş)
- ACILISLAR-2.csv (Uzak geçmiş)

ÇIKTI:
- SIKISMA_PUANI: Ne kadar düşükse, sıkışma o kadar şiddetlidir.
================================================================================
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

# --- AYARLAR ---
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün"  # CSV dosyalarının okunacağı konum
CIKTI_KONUMU = r"C:\Kullanıcılar\RaporKlasörün"  # CSV raporlarının kaydedileceği konum

def sikisma_analizi(ana_dizin):
    print(f"[{ana_dizin}] klasöründeki verilerle sıkışma analizi yapılıyor...")
    
    yol_1 = os.path.join(ana_dizin, 'ACILISLAR-1.csv')
    yol_2 = os.path.join(ana_dizin, 'ACILISLAR-2.csv')
    
    try:
        # 1. Dosyaları Oku
        df1 = pd.read_csv(yol_1)
        df2 = pd.read_csv(yol_2)
        
        # 2. Verileri Birleştir (SEMBOL üzerinden)
        # ACILISLAR-1 ve ACILISLAR-2'yi yan yana getiriyoruz.
        df_full = pd.merge(df1, df2, on='SEMBOL', how='inner')
        
        # 3. Kapanış Fiyatlarını Topla (Son 11 Gün)
        # KAPANIS, KAPANIS-1 ... KAPANIS-10
        kapanis_cols = ['KAPANIS'] + [f'KAPANIS-{i}' for i in range(1, 11)]
        
        # Eğer sütunlar eksikse hata vermemesi için kontrol
        mevcut_cols = [col for col in kapanis_cols if col in df_full.columns]
        
        if len(mevcut_cols) < 5:
            print("HATA: Yeterli geçmiş veri sütunu bulunamadı.")
            return None
            
        # 4. Sıkışma Hesabı (Volatility Ratio)
        # Her satır için (hisse için) standart sapma ve ortalama hesapla
        fiyatlar = df_full[mevcut_cols]
        
        # Standart Sapma (Volatilite)
        df_full['STD_DEV'] = fiyatlar.std(axis=1)
        
        # Ortalama Fiyat
        df_full['ORTALAMA_FIYAT'] = fiyatlar.mean(axis=1)
        
        # Sıkışma Puanı (Düşük olması iyidir)
        # Puan = (Standart Sapma / Ortalama Fiyat) * 100
        df_full['SIKISMA_PUANI'] = (df_full['STD_DEV'] / df_full['ORTALAMA_FIYAT']) * 100
        
        # Ekstra: Son gün hacmi ortalama hacmin altında mı? (Hacim düşüşü sıkışmayı teyit eder)
        # Basitçe son gün hacmi ile önceki günlerin ortalamasını kıyaslayalım
        if 'HACIM' in df_full.columns and 'HACIM-1' in df_full.columns:
             df_full['HACIM_DUSUSU_VAR'] = df_full['HACIM'] < df_full['HACIM-1']
        else:
             df_full['HACIM_DUSUSU_VAR'] = False

        return df_full

    except FileNotFoundError:
        print("HATA: Dosya bulunamadı.")
        return None
    except Exception as e:
        print(f"HATA: {e}")
        return None

# --- ANALİZİ BAŞLAT ---
df_sikisma = sikisma_analizi(DOSYA_KONUMU)

if df_sikisma is not None:
    # Çıktı klasörünü kontrol et ve yoksa oluştur
    if not os.path.exists(CIKTI_KONUMU):
        os.makedirs(CIKTI_KONUMU)
        print(f"✓ Çıktı klasörü oluşturuldu: {CIKTI_KONUMU}")
    
    # Zaman damgası
    zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # FİLTRELEME: En sıkışık hisseler (Puanı en düşük olanlar)
    # Genelde %1-2 altı çok ciddi sıkışmadır.
    en_sikisik = df_sikisma.sort_values(by='SIKISMA_PUANI', ascending=True).head(15)
    
    cols_to_show = ['SEMBOL', 'KAPANIS', 'SIKISMA_PUANI', 'HACIM_DUSUSU_VAR']
    
    print("\n" + "="*75)
    print(" EN FAZLA SIKIŞAN (PATLAMAYA HAZIR) HİSSELER")
    print("="*75)
    
    pd.options.display.float_format = '{:,.2f}'.format
    print(en_sikisik[cols_to_show].to_string(index=False))
    
    # CSV olarak kaydet
    # 1. Tüm Sıkışma Analizi
    tum_dosya = os.path.join(CIKTI_KONUMU, f'SIKISMA_ALANI_TUM_{zaman_damgasi}.csv')
    df_sikisma[['SEMBOL', 'KAPANIS', 'SIKISMA_PUANI', 'STD_DEV', 'ORTALAMA_FIYAT', 'HACIM_DUSUSU_VAR']].sort_values(by='SIKISMA_PUANI', ascending=True).to_csv(tum_dosya, index=False, encoding='utf-8-sig')
    print(f"\n✓ Tüm sıkışma analizi: {tum_dosya}")
    
    # 2. En Sıkışık 15
    sikisik_dosya = os.path.join(CIKTI_KONUMU, f'SIKISMA_ALANI_EN_SIKISIK_{zaman_damgasi}.csv')
    en_sikisik[cols_to_show].to_csv(sikisik_dosya, index=False, encoding='utf-8-sig')
    print(f"✓ En sıkışık hisseler: {sikisik_dosya}")
    
    print("\n[YORUM]: 'SIKISMA_PUANI' ne kadar 0'a yakınsa, fiyat o kadar yatay ve sıkışıktır.")
    print("Bu hisseler yakında bir yöne (aşağı veya yukarı) sert kırılım yapabilir.")
    print("Kırılım yönünü tayin etmek için 'Kademeler Arası Denge' kodunu kullanabilirsin.")
    
    print("\n" + "="*75)
    print(" ANALİZ TAMAMLANDI - RAPORLAR CSV OLARAK KAYDEDİLDİ")
    print("="*75)