"""
================================================================================
PROJE ADI   : Otomatik Derinlik Analizi (Depth Imbalance Algorithm)
YAZAR       : Borsa (AI Assistant)
VERSIYON    : 2.0

AÇIKLAMA:
Bu script, hisselerin derinlik verilerini tarayarak arz-talep dengesini ölçer.
Hangi hissenin arkasında "Alıcı Rüzgarı", hangisinin önünde "Satıcı Duvarı"
olduğunu tespit eder.

KULLANILAN METRİKLER:
1. DERİNLİK ORANI = Toplam Alış Lotu / Toplam Satış Lotu
2. MAJOR DESTEK/DİRENÇ = En yüksek hacimli bekleyen emir seviyeleri.
================================================================================
"""

import pandas as pd
import os

# --- AYARLAR ---
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün" 
KADEME_DERINLIGI = 14  # Kaç kademe analiz edilecek?

def otomatik_derinlik_analizi(ana_dizin, derinlik_siniri):
    print(f"[{ana_dizin}] klasöründeki derinlik verileri taranıyor...")
    
    yol_alis = os.path.join(ana_dizin, 'DERINLIK_ALIS-1.csv')
    yol_satis = os.path.join(ana_dizin, 'DERINLIK_SATIS-1.csv')
    
    try:
        # Dosyaları Oku
        df_alis = pd.read_csv(yol_alis)
        df_satis = pd.read_csv(yol_satis)
        
        # Alış ve Satış tablolarını 'SEMBOL' üzerinden birleştir
        # suffixes parametresi, çakışan sütun isimlerine _ALIS ve _SATIS ekler
        df = pd.merge(df_alis, df_satis, on='SEMBOL', how='inner', suffixes=('_ALIS', '_SATIS'))
        
        sonuclar = []

        # Her hisse için döngü
        for index, row in df.iterrows():
            sembol = row['SEMBOL']
            
            toplam_alis_lot = 0
            toplam_satis_lot = 0
            
            en_guclu_destek_fiyat = 0
            en_guclu_destek_lot = 0
            
            en_guclu_direnc_fiyat = 0
            en_guclu_direnc_lot = 0
            
            # --- ALIŞ (DESTEK) TARAFI ANALİZİ ---
            for i in range(1, derinlik_siniri + 1):
                col_adet = f"{i} ALIS ADET"
                col_fiyat = f"{i} ALIS"
                # Dosyada bu sütun var mı diye bak (Hata almamak için)
                if col_adet in row and col_fiyat in row:
                    adet = row[col_adet]
                    fiyat = row[col_fiyat]
                    
                    if pd.notna(adet):
                        toplam_alis_lot += adet
                        # En büyük yığılmayı bul (Major Destek)
                        if adet > en_guclu_destek_lot:
                            en_guclu_destek_lot = adet
                            en_guclu_destek_fiyat = fiyat

            # --- SATIŞ (DİRENÇ) TARAFI ANALİZİ ---
            for i in range(1, derinlik_siniri + 1):
                col_adet = f"{i} SATIS ADET"
                col_fiyat = f"{i} SATIS"
                
                if col_adet in row and col_fiyat in row:
                    adet = row[col_adet]
                    fiyat = row[col_fiyat]
                    
                    if pd.notna(adet):
                        toplam_satis_lot += adet
                        # En büyük yığılmayı bul (Major Direnç)
                        if adet > en_guclu_direnc_lot:
                            en_guclu_direnc_lot = adet
                            en_guclu_direnc_fiyat = fiyat

            # --- HESAPLAMA VE KARAR MEKANİZMASI ---
            if toplam_satis_lot > 0:
                derinlik_orani = toplam_alis_lot / toplam_satis_lot
            elif toplam_alis_lot > 0:
                derinlik_orani = 100 # Satıcı yok, tavan olabilir
            else:
                derinlik_orani = 0 # Veri yok
            
            net_fark = toplam_alis_lot - toplam_satis_lot
            
            # Durum Etiketi Ata
            durum = "DENGELİ"
            if derinlik_orani > 2.0: durum = "GÜÇLÜ BOĞA (ALICI ÇOK)"
            elif derinlik_orani > 1.2: durum = "ALICI AĞIRLIKLI"
            elif derinlik_orani < 0.5: durum = "GÜÇLÜ AYI (SATICI ÇOK)"
            elif derinlik_orani < 0.8: durum = "SATICI AĞIRLIKLI"

            sonuclar.append({
                'SEMBOL': sembol,
                'DURUM': durum,
                'DERINLIK_ORANI': derinlik_orani,
                'TOPLAM_ALIS_LOT': int(toplam_alis_lot),
                'TOPLAM_SATIS_LOT': int(toplam_satis_lot),
                'NET_FARK_LOT': int(net_fark),
                'MAJOR_DESTEK': en_guclu_destek_fiyat,
                'MAJOR_DIRENC': en_guclu_direnc_fiyat
            })
            
        return pd.DataFrame(sonuclar)

    except FileNotFoundError:
        print("HATA: Derinlik dosyaları bulunamadı.")
        return None
    except Exception as e:
        print(f"HATA: {e}")
        return None

# --- ANALİZİ BAŞLAT ---
df_derinlik = otomatik_derinlik_analizi(DOSYA_KONUMU, KADEME_DERINLIGI)

if df_derinlik is not None:
    # 1. ALICI AĞIRLIKLI HİSSELER (YÜKSELİŞ POTANSİYELİ)
    # Derinlik Oranı en yüksek olanlar
    alicili = df_derinlik.sort_values(by='DERINLIK_ORANI', ascending=False).head(15)
    
    print("\n" + "="*85)
    print(" ALICI BASKISI EN YÜKSEK HİSSELER (BOĞA PİYASASI ADAYLARI)")
    print("="*85)
    print(alicili[['SEMBOL', 'DURUM', 'DERINLIK_ORANI', 'NET_FARK_LOT', 'MAJOR_DESTEK', 'MAJOR_DIRENC']].to_string(index=False))
    
    # 2. SATICI AĞIRLIKLI HİSSELER (DÜŞÜŞ RİSKİ)
    # Derinlik Oranı en düşük olanlar (0'a yakın)
    saticili = df_derinlik[df_derinlik['DERINLIK_ORANI'] > 0].sort_values(by='DERINLIK_ORANI', ascending=True).head(15)
    
    print("\n" + "="*85)
    print(" SATICI BASKISI EN YÜKSEK HİSSELER (AYI PİYASASI ADAYLARI)")
    print("="*85)
    print(saticili[['SEMBOL', 'DURUM', 'DERINLIK_ORANI', 'NET_FARK_LOT', 'MAJOR_DESTEK', 'MAJOR_DIRENC']].to_string(index=False))

    print("\n[YORUM]: 'DERINLIK_ORANI' 1.0 ise alıcılar ve satıcılar eşittir.")
    print("Oran 5.0 ise, her 1 satıcıya karşılık 5 alıcı var demektir (Çok Güçlü).")