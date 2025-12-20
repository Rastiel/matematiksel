"""
================================================================================
PROJE ADI   : Likidite Duvarı Analizi (Liquidity Wall Detector)
YAZAR       : Borsa (AI Assistant)
VERSIYON    : 1.0

AÇIKLAMA:
Bu script, tahtadaki 'Anormal Emir Yığılmalarını' (Duvarları) tespit eder.
Bir kademedeki lot miktarı, tahtanın geri kalanının ortalamasının
belirli bir katıysa (Örn: 4 katı), orayı "DUVAR" olarak işaretler.

PARAMETRE:
- DUVAR_CARPANI: Bir kademe, ortalamanın kaç katıysa duvar kabul edilsin? (Varsayılan: 4x)
================================================================================
"""

import pandas as pd
import os

# --- AYARLAR ---
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün" 
KADEME_DERINLIGI = 14
DUVAR_CARPANI = 4.0  # Ortalamanın 4 katı büyüklükteyse "Duvar" de.

def likidite_duvari_analizi(ana_dizin, derinlik_siniri, carpan):
    print(f"[{ana_dizin}] klasöründe {carpan}x büyüklüğündeki duvarlar taranıyor...")
    
    yol_alis = os.path.join(ana_dizin, 'DERINLIK_ALIS-1.csv')
    yol_satis = os.path.join(ana_dizin, 'DERINLIK_SATIS-1.csv')
    yol_fiyat = os.path.join(ana_dizin, 'ACILISLAR-1.csv')
    
    try:
        df_alis = pd.read_csv(yol_alis)
        df_satis = pd.read_csv(yol_satis)
        
        # Fiyat bilgisini de alalım (Duvarın fiyata uzaklığını ölçmek için)
        if os.path.exists(yol_fiyat):
            df_fiyat = pd.read_csv(yol_fiyat)[['SEMBOL', 'KAPANIS']]
        else:
            df_fiyat = pd.DataFrame(columns=['SEMBOL', 'KAPANIS'])
            
        # Birleştir
        df = pd.merge(df_alis, df_satis, on='SEMBOL', how='inner', suffixes=('_ALIS', '_SATIS'))
        df = pd.merge(df, df_fiyat, on='SEMBOL', how='left')
        
        sonuclar = []

        for index, row in df.iterrows():
            sembol = row['SEMBOL']
            kapanis = row['KAPANIS']
            
            # --- ALIŞ TARAFI (DESTEK DUVARI) ---
            alis_lotlari = []
            alis_fiyatlari = []
            for i in range(1, derinlik_siniri + 1):
                col_adet = f"{i} ALIS ADET"
                col_fiyat = f"{i} ALIS"
                if col_adet in row and pd.notna(row[col_adet]):
                    alis_lotlari.append(row[col_adet])
                    alis_fiyatlari.append(row[col_fiyat])
            
            # Analiz
            if len(alis_lotlari) > 0:
                ort_alis = sum(alis_lotlari) / len(alis_lotlari)
                max_alis = max(alis_lotlari)
                max_index = alis_lotlari.index(max_alis)
                duvar_fiyati_alis = alis_fiyatlari[max_index]
                
                # Duvar mı? (Max Lot > Ortalama * Çarpan)
                if max_alis > (ort_alis * carpan):
                    duvar_gucu = max_alis / ort_alis
                    uzaklik = (kapanis - duvar_fiyati_alis) / kapanis * 100 if kapanis else 0
                    
                    sonuclar.append({
                        'SEMBOL': sembol,
                        'YON': 'ALIS (DESTEK)',
                        'DUVAR_FIYATI': duvar_fiyati_alis,
                        'DUVAR_LOTU': int(max_alis),
                        'DUVAR_GUCU_KAT': round(duvar_gucu, 1),
                        'FIYATA_UZAKLIK_%': round(uzaklik, 2),
                        'KAPANIS': kapanis
                    })

            # --- SATIŞ TARAFI (DİRENÇ DUVARI) ---
            satis_lotlari = []
            satis_fiyatlari = []
            for i in range(1, derinlik_siniri + 1):
                col_adet = f"{i} SATIS ADET"
                col_fiyat = f"{i} SATIS"
                if col_adet in row and pd.notna(row[col_adet]):
                    satis_lotlari.append(row[col_adet])
                    satis_fiyatlari.append(row[col_fiyat])
            
            # Analiz
            if len(satis_lotlari) > 0:
                ort_satis = sum(satis_lotlari) / len(satis_lotlari)
                max_satis = max(satis_lotlari)
                max_index = satis_lotlari.index(max_satis)
                duvar_fiyati_satis = satis_fiyatlari[max_index]
                
                # Duvar mı?
                if max_satis > (ort_satis * carpan):
                    duvar_gucu = max_satis / ort_satis
                    uzaklik = (duvar_fiyati_satis - kapanis) / kapanis * 100 if kapanis else 0
                    
                    sonuclar.append({
                        'SEMBOL': sembol,
                        'YON': 'SATIS (DIRENC)',
                        'DUVAR_FIYATI': duvar_fiyati_satis,
                        'DUVAR_LOTU': int(max_satis),
                        'DUVAR_GUCU_KAT': round(duvar_gucu, 1),
                        'FIYATA_UZAKLIK_%': round(uzaklik, 2),
                        'KAPANIS': kapanis
                    })
                    
        return pd.DataFrame(sonuclar)

    except Exception as e:
        print(f"HATA: {e}")
        return None

# --- ANALİZİ BAŞLAT ---
df_duvar = likidite_duvari_analizi(DOSYA_KONUMU, KADEME_DERINLIGI, DUVAR_CARPANI)

if df_duvar is not None:
    # 1. EN BÜYÜK DESTEK DUVARLARI (Alış Yönü)
    buy_walls = df_duvar[df_duvar['YON'] == 'ALIS (DESTEK)'].sort_values(by='DUVAR_GUCU_KAT', ascending=False).head(10)
    
    print("\n" + "="*85)
    print(f" TESPİT EDİLEN EN GÜÇLÜ ALIŞ DUVARLARI (ORTALAMANIN EN AZ {DUVAR_CARPANI} KATI)")
    print("="*85)
    print(buy_walls[['SEMBOL', 'DUVAR_FIYATI', 'DUVAR_LOTU', 'DUVAR_GUCU_KAT', 'FIYATA_UZAKLIK_%']].to_string(index=False))
    
    # 2. EN BÜYÜK DİRENÇ DUVARLARI (Satış Yönü)
    sell_walls = df_duvar[df_duvar['YON'] == 'SATIS (DIRENC)'].sort_values(by='DUVAR_GUCU_KAT', ascending=False).head(10)
    
    print("\n" + "="*85)
    print(f" TESPİT EDİLEN EN GÜÇLÜ SATIŞ DUVARLARI (ORTALAMANIN EN AZ {DUVAR_CARPANI} KATI)")
    print("="*85)
    print(sell_walls[['SEMBOL', 'DUVAR_FIYATI', 'DUVAR_LOTU', 'DUVAR_GUCU_KAT', 'FIYATA_UZAKLIK_%']].to_string(index=False))

    print("\n[STRATEJİ]: 'DUVAR_GUCU_KAT' ne kadar yüksekse (örn: 10x), o seviye o kadar zor kırılır.")
    print("Alış Duvarının hemen 1 kademe üzerine 'ALIM', Satış Duvarının 1 kademe altına 'SATIM/STOP' yazılır.")