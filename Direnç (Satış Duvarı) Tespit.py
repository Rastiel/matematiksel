"""
================================================================================
PROJE ADI   : Direnç (Satış Duvarı) Tespit Robotu (Genişletilmiş)
YAZAR       : Borsa (AI Assistant)
VERSIYON    : 1.2 (CSV Çıktılı)

AÇIKLAMA:
Bu script, satış tarafındaki derinliği analiz eder. 
'KADEME_DERINLIGI' ayarı ile kaç kademe (10, 14, 20 vb.) taranacağı belirlenir.
================================================================================
"""

import pandas as pd
import os
from datetime import datetime

# --- AYARLAR ---
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün"  # CSV dosyalarının okunacağı konum
CIKTI_KONUMU = r"C:\Kullanıcılar\RaporKlasörün"  # CSV raporlarının kaydedileceği konum

# Analiz etmek istediğin kademe sayısı (Senin dosyan 14'lü olduğu için 14 yaptık)
KADEME_DERINLIGI = 14 

def direnc_analizi(ana_dizin, derinlik_siniri):
    print(f"[{ana_dizin}] klasöründeki veriler {derinlik_siniri} kademe derinliğinde taranıyor...")
    
    yol_derinlik = os.path.join(ana_dizin, 'DERINLIK_SATIS-1.csv')
    
    try:
        df = pd.read_csv(yol_derinlik)
        
        sonuclar = []

        for index, row in df.iterrows():
            sembol = row['SEMBOL']
            
            en_yuksek_lot = 0
            en_guclu_fiyat = 0
            toplam_baski = 0
            
            # 1'den başlayıp belirlenen sınıra kadar döngü kuruyoruz (1..15 -> 14 dahil)
            for i in range(1, derinlik_siniri + 1): 
                try:
                    # Sütun isimlerini dinamik oluşturuyoruz: "14 SATIS ADET" gibi
                    adet_col = f"{i} SATIS ADET"
                    fiyat_col = f"{i} SATIS"
                    
                    # Eğer dosya içinde bu sütun varsa işle (Yoksa hata vermez, atlar)
                    if adet_col in df.columns and fiyat_col in df.columns:
                        adet = row[adet_col]
                        fiyat = row[fiyat_col]
                        
                        if pd.notna(adet) and pd.notna(fiyat):
                            toplam_baski += adet
                            
                            # En güçlü direnç kademesini güncelle
                            if adet > en_yuksek_lot:
                                en_yuksek_lot = adet
                                en_guclu_fiyat = fiyat
                except:
                    continue 
            
            sonuclar.append({
                'SEMBOL': sembol,
                'MAJOR_DIRENC_FIYATI': en_guclu_fiyat,
                'DIRENC_LOT_MIKTARI': int(en_yuksek_lot),
                'TOPLAM_SATIS_BASKISI': int(toplam_baski)
            })
            
        return pd.DataFrame(sonuclar)

    except FileNotFoundError:
        print("HATA: Dosya bulunamadı.")
        return None
    except Exception as e:
        print(f"HATA: {e}")
        return None

# --- ANALİZİ BAŞLAT ---
df_direnc = direnc_analizi(DOSYA_KONUMU, KADEME_DERINLIGI)

if df_direnc is not None:
    # Çıktı klasörünü kontrol et ve yoksa oluştur
    if not os.path.exists(CIKTI_KONUMU):
        os.makedirs(CIKTI_KONUMU)
        print(f"✓ Çıktı klasörü oluşturuldu: {CIKTI_KONUMU}")
    
    # Zaman damgası
    zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    en_baskili = df_direnc.sort_values(by='TOPLAM_SATIS_BASKISI', ascending=False).head(10)
    
    print(f"\n{'='*65}")
    print(f" {KADEME_DERINLIGI} KADEMEDE EN YOĞUN SATIŞ BASKISI OLAN HİSSELER")
    print(f"{'='*65}")
    print(en_baskili.to_string(index=False))
    
    # CSV olarak kaydet
    # 1. Tüm Direnç Analizi
    tum_dosya = os.path.join(CIKTI_KONUMU, f'DIRENC_DUVARI_TUM_{zaman_damgasi}.csv')
    df_direnc.sort_values(by='TOPLAM_SATIS_BASKISI', ascending=False).to_csv(tum_dosya, index=False, encoding='utf-8-sig')
    print(f"\n✓ Tüm direnç analizi: {tum_dosya}")
    
    # 2. En Baskılı 10
    en_baskili_dosya = os.path.join(CIKTI_KONUMU, f'DIRENC_DUVARI_EN_BASKILI_{zaman_damgasi}.csv')
    en_baskili.to_csv(en_baskili_dosya, index=False, encoding='utf-8-sig')
    print(f"✓ En baskılı 10 direnç: {en_baskili_dosya}")
    
    print("\n" + "="*65)
    print(" ANALİZ TAMAMLANDI - RAPORLAR CSV OLARAK KAYDEDİLDİ")
    print("="*65)