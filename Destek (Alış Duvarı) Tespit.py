"""
================================================================================
PROJE ADI   : Destek (Alış Duvarı) Tespit Robotu
YAZAR       : Borsa (AI Assistant)
VERSIYON    : 1.2 (CSV Çıktılı)

AÇIKLAMA:
Bu script, 'DERINLIK_ALIS' verisini kullanarak hisselerin altındaki en güçlü 
destek seviyelerini ve toplam alıcı iştahını tespit eder.

ÇIKTI:
- Hisse bazında en yüklü alışın beklediği fiyat seviyesi (Major Destek).
- İlk 14 kademedeki toplam alış desteği (Duvarın Kalınlığı).
================================================================================
"""

import pandas as pd
import os
from datetime import datetime

# --- AYARLAR ---
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün"  # CSV dosyalarının okunacağı konum
CIKTI_KONUMU = r"C:\Kullanıcılar\RaporKlasörün"  # CSV raporlarının kaydedileceği konum
KADEME_DERINLIGI = 14  # Kaç kademe taranacak?

def destek_analizi(ana_dizin, derinlik_siniri):
    print(f"[{ana_dizin}] klasöründeki veriler {derinlik_siniri} kademe derinliğinde taranıyor...")
    
    yol_derinlik = os.path.join(ana_dizin, 'DERINLIK_ALIS-1.csv')
    
    try:
        df = pd.read_csv(yol_derinlik)
        
        sonuclar = []

        for index, row in df.iterrows():
            sembol = row['SEMBOL']
            
            en_yuksek_lot = 0
            en_guclu_fiyat = 0
            toplam_destek = 0
            
            # 1'den başlayıp belirlenen sınıra kadar (1..14)
            for i in range(1, derinlik_siniri + 1): 
                try:
                    # Sütun isimleri: "1 ALIS ADET", "1 ALIS"
                    adet_col = f"{i} ALIS ADET"
                    fiyat_col = f"{i} ALIS"
                    
                    if adet_col in df.columns and fiyat_col in df.columns:
                        adet = row[adet_col]
                        fiyat = row[fiyat_col]
                        
                        if pd.notna(adet) and pd.notna(fiyat):
                            toplam_destek += adet
                            
                            # En yüklü kademeyi bul
                            if adet > en_yuksek_lot:
                                en_yuksek_lot = adet
                                en_guclu_fiyat = fiyat
                except:
                    continue 
            
            sonuclar.append({
                'SEMBOL': sembol,
                'MAJOR_DESTEK_FIYATI': en_guclu_fiyat,
                'DESTEK_LOT_MIKTARI': int(en_yuksek_lot),
                'TOPLAM_ALIS_DESTEGI': int(toplam_destek)
            })
            
        return pd.DataFrame(sonuclar)

    except FileNotFoundError:
        print("HATA: Dosya bulunamadı.")
        return None
    except Exception as e:
        print(f"HATA: {e}")
        return None

# --- ANALİZİ BAŞLAT ---
df_destek = destek_analizi(DOSYA_KONUMU, KADEME_DERINLIGI)

if df_destek is not None:
    # Çıktı klasörünü kontrol et ve yoksa oluştur
    if not os.path.exists(CIKTI_KONUMU):
        os.makedirs(CIKTI_KONUMU)
        print(f"✓ Çıktı klasörü oluşturuldu: {CIKTI_KONUMU}")
    
    # Zaman damgası
    zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Filtreleme: En Güçlü Alış Desteği Olanlar (Güvenli Limanlar)
    en_saglam = df_destek.sort_values(by='TOPLAM_ALIS_DESTEGI', ascending=False).head(10)
    
    print(f"\n{'='*65}")
    print(f" {KADEME_DERINLIGI} KADEMEDE EN GÜÇLÜ ALICI DESTEĞİ OLAN HİSSELER")
    print(f"{'='*65}")
    print(en_saglam.to_string(index=False))
    
    # CSV olarak kaydet
    # 1. Tüm Destek Analizi
    tum_dosya = os.path.join(CIKTI_KONUMU, f'DESTEK_DUVARI_TUM_{zaman_damgasi}.csv')
    df_destek.sort_values(by='TOPLAM_ALIS_DESTEGI', ascending=False).to_csv(tum_dosya, index=False, encoding='utf-8-sig')
    print(f"\n✓ Tüm destek analizi: {tum_dosya}")
    
    # 2. En Güçlü 10
    en_saglam_dosya = os.path.join(CIKTI_KONUMU, f'DESTEK_DUVARI_EN_GUCLU_{zaman_damgasi}.csv')
    en_saglam.to_csv(en_saglam_dosya, index=False, encoding='utf-8-sig')
    print(f"✓ En güçlü 10 destek: {en_saglam_dosya}")
    
    # Yorumlama
    print("\n[STRATEJİ]: 'MAJOR_DESTEK_FIYATI', olası düşüşlerde 'Tepki Alımı' gelmesi muhtemel yerdir.")
    print("Alım emri girmek için bu seviyeler veya bir kademe üstü tercih edilebilir.")
    
    print("\n" + "="*65)
    print(" ANALİZ TAMAMLANDI - RAPORLAR CSV OLARAK KAYDEDİLDİ")
    print("="*65)