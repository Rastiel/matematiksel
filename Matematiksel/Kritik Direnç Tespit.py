"""
================================================================================
PROJE ADI   : Kritik Direnç Tespit Robotu (Teknik + Derinlik)
YAZAR       : Borsa (AI Assistant)
VERSIYON    : 1.4

AÇIKLAMA:
Bu script, hisselerin yükseliş yolundaki en ciddi engelleri bulur.
Hem geçmiş fiyat hareketlerindeki zirveleri (Teknik Direnç),
hem de anlık tahtadaki satış yığılmalarını (Derinlik Direnci) analiz eder.

MANTIK:
1. Teknik Direnç = Son 5 günün en yüksek fiyatı (YUKSEK sütunları)
2. Derinlik Direnci = Tahtada en çok satış lotunun beklediği fiyat
3. KRİTİK SEVİYE = Eğer bu iki seviye birbirine çok yakınsa (%1 fark),
   orası çok güçlü bir satış bölgesidir.

VERİ KAYNAĞI:
- ACILISLAR-1.csv (Fiyat Geçmişi)
- DERINLIK_SATIS-1.csv (Anlık Satıcılar)
================================================================================
"""

import pandas as pd
import os
import numpy as np

# --- AYARLAR ---
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün" 
KADEME_DERINLIGI = 14

def kritik_direnc_analizi(ana_dizin, derinlik_siniri):
    print(f"[{ana_dizin}] üzerinde kritik direnç analizi yapılıyor...")
    
    yol_fiyat = os.path.join(ana_dizin, 'ACILISLAR-1.csv')
    yol_derinlik = os.path.join(ana_dizin, 'DERINLIK_SATIS-1.csv')
    
    try:
        df_fiyat = pd.read_csv(yol_fiyat)
        df_derinlik = pd.read_csv(yol_derinlik)
        
        sonuclar = []

        # Her hisse için döngü
        for index, row in df_derinlik.iterrows():
            sembol = row['SEMBOL']
            
            # --- 1. DERİNLİK ANALİZİ (TAHTADAKİ DUVAR) ---
            en_yuksek_lot = 0
            duvar_fiyati = 0
            
            for i in range(1, derinlik_siniri + 1):
                try:
                    col_adet = f"{i} SATIS ADET"
                    col_fiyat = f"{i} SATIS"
                    if col_adet in df_derinlik.columns and col_fiyat in df_derinlik.columns:
                        adet = row[col_adet]
                        fiyat = row[col_fiyat]
                        
                        if pd.notna(adet) and adet > en_yuksek_lot:
                            en_yuksek_lot = adet
                            duvar_fiyati = fiyat
                except:
                    continue
            
            # --- 2. TEKNİK ANALİZ (GEÇMİŞ ZİRVE) ---
            # ACILISLAR dosyasından o hisseyi bul
            fiyat_data = df_fiyat[df_fiyat['SEMBOL'] == sembol]
            
            if not fiyat_data.empty:
                # Son 5 günün en yükseğini bul: YUKSEK, YUKSEK-1 ... YUKSEK-4
                cols_yuksek = ['YUKSEK'] + [f'YUKSEK-{i}' for i in range(1, 5)]
                mevcut_cols = [c for c in cols_yuksek if c in df_fiyat.columns]
                
                gecmis_zirve = fiyat_data[mevcut_cols].max(axis=1).values[0]
                guncel_fiyat = fiyat_data['KAPANIS'].values[0]
                
                # --- 3. ÇAKIŞMA KONTROLÜ ---
                # Derinlik Duvarı ile Geçmiş Zirve birbirine yakın mı?
                fark_yuzde = abs(duvar_fiyati - gecmis_zirve) / gecmis_zirve * 100
                
                # Direnç şu anki fiyattan ne kadar uzak?
                dirence_uzaklik = (duvar_fiyati - guncel_fiyat) / guncel_fiyat * 100
                
                sonuclar.append({
                    'SEMBOL': sembol,
                    'GUNCEL_FIYAT': guncel_fiyat,
                    'TEKNIK_ZIRVE_5G': gecmis_zirve,
                    'TAHTA_SATIS_DUVARI': duvar_fiyati,
                    'DUVARDAKI_LOT': int(en_yuksek_lot),
                    'CAKISMA_DURUMU': 'VAR' if fark_yuzde < 1.0 else 'YOK', # %1'den az fark varsa çakışma var
                    'DIRENCE_UZAKLIK_YUZDE': dirence_uzaklik
                })
        
        return pd.DataFrame(sonuclar)

    except FileNotFoundError:
        print("HATA: Dosya bulunamadı.")
        return None
    except Exception as e:
        print(f"HATA: {e}")
        return None

# --- ANALİZİ BAŞLAT ---
df_kritik = kritik_direnc_analizi(DOSYA_KONUMU, KADEME_DERINLIGI)

if df_kritik is not None:
    # FİLTRE: "ÇAKIŞMA VAR" olanlar (En Güçlü Dirençler)
    cakisanlar = df_kritik[
        (df_kritik['CAKISMA_DURUMU'] == 'VAR') &
        (df_kritik['DIRENCE_UZAKLIK_YUZDE'] > 0) # Fiyat direncin altındaysa
    ].sort_values(by='DUVARDAKI_LOT', ascending=False)
    
    cols = ['SEMBOL', 'GUNCEL_FIYAT', 'TEKNIK_ZIRVE_5G', 'TAHTA_SATIS_DUVARI', 'DUVARDAKI_LOT', 'DIRENCE_UZAKLIK_YUZDE']
    
    print("\n" + "="*85)
    print(" KRİTİK DİRENÇLER (TEKNİK ZİRVE VE SATIŞ DUVARI ÇAKIŞANLAR)")
    print("="*85)
    
    pd.options.display.float_format = '{:,.2f}'.format
    print(cakisanlar[cols].head(15).to_string(index=False))
    
    print("\n[YORUM]: Bu hisselerde 'TAHTA_SATIS_DUVARI' fiyatı geçilmesi çok zor bir barajdır.")
    print("Satış hedefi koyarken bu seviyenin 1-2 kademe altını kullanmak mantıklı olabilir.")