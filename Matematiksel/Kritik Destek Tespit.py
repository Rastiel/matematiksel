"""
================================================================================
PROJE ADI   : Kritik Destek Tespit Robotu (Beton Zemin Analizi)
YAZAR       : Borsa (AI Assistant)
VERSIYON    : 1.5

AÇIKLAMA:
Bu script, hisselerin düşüşte tutunabileceği en güçlü destekleri bulur.
Hem geçmiş fiyat hareketlerindeki dipleri (Teknik Destek),
hem de anlık tahtadaki alış yığılmalarını (Derinlik Desteği) analiz eder.

MANTIK:
1. Teknik Destek = Son 5 günün en düşük fiyatı (DUSUK sütunları)
2. Derinlik Desteği = Tahtada en çok alış lotunun beklediği fiyat
3. KRİTİK SEVİYE = Eğer bu iki seviye birbirine çok yakınsa (%1 fark),
   orası çok güvenli bir alım bölgesidir.

VERİ KAYNAĞI:
- ACILISLAR-1.csv (Fiyat Geçmişi)
- DERINLIK_ALIS-1.csv (Anlık Alıcılar)
================================================================================
"""

import pandas as pd
import os
import numpy as np

# --- AYARLAR ---
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün" 
KADEME_DERINLIGI = 14

def kritik_destek_analizi(ana_dizin, derinlik_siniri):
    print(f"[{ana_dizin}] üzerinde kritik destek analizi yapılıyor...")
    
    yol_fiyat = os.path.join(ana_dizin, 'ACILISLAR-1.csv')
    yol_derinlik = os.path.join(ana_dizin, 'DERINLIK_ALIS-1.csv')
    
    try:
        df_fiyat = pd.read_csv(yol_fiyat)
        df_derinlik = pd.read_csv(yol_derinlik)
        
        sonuclar = []

        # Her hisse için döngü (Derinlik dosyasındaki her satır)
        for index, row in df_derinlik.iterrows():
            sembol = row['SEMBOL']
            
            # --- 1. DERİNLİK ANALİZİ (TAHTADAKİ ALICI DUVARI) ---
            en_yuksek_lot = 0
            duvar_fiyati = 0
            
            for i in range(1, derinlik_siniri + 1):
                try:
                    col_adet = f"{i} ALIS ADET"
                    col_fiyat = f"{i} ALIS"
                    # Sütun var mı kontrol et
                    if col_adet in df_derinlik.columns and col_fiyat in df_derinlik.columns:
                        adet = row[col_adet]
                        fiyat = row[col_fiyat]
                        
                        if pd.notna(adet) and adet > en_yuksek_lot:
                            en_yuksek_lot = adet
                            duvar_fiyati = fiyat
                except:
                    continue
            
            # --- 2. TEKNİK ANALİZ (GEÇMİŞ DİP) ---
            fiyat_data = df_fiyat[df_fiyat['SEMBOL'] == sembol]
            
            if not fiyat_data.empty:
                # Son 5 günün en düşüğünü bul: DUSUK, DUSUK-1 ... DUSUK-4
                cols_dusuk = ['DUSUK'] + [f'DUSUK-{i}' for i in range(1, 5)]
                mevcut_cols = [c for c in cols_dusuk if c in df_fiyat.columns]
                
                if mevcut_cols:
                    gecmis_dip = fiyat_data[mevcut_cols].min(axis=1).values[0]
                    guncel_fiyat = fiyat_data['KAPANIS'].values[0]
                    
                    # --- 3. ÇAKIŞMA KONTROLÜ ---
                    # Alış Duvarı ile Geçmiş Dip birbirine yakın mı?
                    if duvar_fiyati > 0:
                        fark_yuzde = abs(duvar_fiyati - gecmis_dip) / gecmis_dip * 100
                        
                        # Destek şu anki fiyattan ne kadar aşağıda?
                        destege_uzaklik = (guncel_fiyat - duvar_fiyati) / guncel_fiyat * 100
                        
                        sonuclar.append({
                            'SEMBOL': sembol,
                            'GUNCEL_FIYAT': guncel_fiyat,
                            'TEKNIK_DIP_5G': gecmis_dip,
                            'TAHTA_ALIS_DUVARI': duvar_fiyati,
                            'DUVARDAKI_LOT': int(en_yuksek_lot),
                            'CAKISMA_DURUMU': 'VAR' if fark_yuzde < 1.0 else 'YOK', # %1'den az fark varsa
                            'DESTEGE_UZAKLIK_YUZDE': destege_uzaklik
                        })
        
        return pd.DataFrame(sonuclar)

    except FileNotFoundError:
        print("HATA: Dosya bulunamadı.")
        return None
    except Exception as e:
        print(f"HATA: {e}")
        return None

# --- ANALİZİ BAŞLAT ---
df_kritik_destek = kritik_destek_analizi(DOSYA_KONUMU, KADEME_DERINLIGI)

if df_kritik_destek is not None:
    # FİLTRE: "ÇAKIŞMA VAR" olanlar (En Sağlam Destekler)
    # Ayrıca desteğe yakın olanları öne çıkaralım (Alım fırsatı)
    saglam_destekler = df_kritik_destek[
        (df_kritik_destek['CAKISMA_DURUMU'] == 'VAR') &
        (df_kritik_destek['DESTEGE_UZAKLIK_YUZDE'] > 0) # Fiyat desteğin üzerindeyse
    ].sort_values(by='DESTEGE_UZAKLIK_YUZDE', ascending=True) # En yakın olan en üstte
    
    cols = ['SEMBOL', 'GUNCEL_FIYAT', 'TEKNIK_DIP_5G', 'TAHTA_ALIS_DUVARI', 'DUVARDAKI_LOT', 'DESTEGE_UZAKLIK_YUZDE']
    
    print("\n" + "="*85)
    print(" KRİTİK DESTEKLER (TEKNİK DİP VE ALIŞ DUVARI ÇAKIŞANLAR)")
    print("="*85)
    
    pd.options.display.float_format = '{:,.2f}'.format
    print(saglam_destekler[cols].head(15).to_string(index=False))
    
    print("\n[STRATEJİ]: 'DESTEGE_UZAKLIK_YUZDE' ne kadar düşükse (örn: %0.5), hisse desteğe o kadar yakındır.")
    print("Bu seviyeler 'Stop-Loss' koymak veya tepki alımı denemek için idealdir.")