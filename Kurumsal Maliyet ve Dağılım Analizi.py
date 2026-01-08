"""
================================================================================
PROJE ADI   : Kurumsal Maliyet ve Dağılım Analizi (Smart Money Tracker)
YAZAR       : Borsa (AI Assistant)
VERSIYON    : 1.4 (CSV Çıktılı)

AÇIKLAMA:
Bu script, hisseleri toplayan aracı kurumları analiz eder.
Özellikle 'Yabancı' ve 'Kurumsal' alımların maliyetini hesaplayarak, 
fiyatın bu maliyete ne kadar yakın olduğunu (Fırsat Bölgesi) tespit eder.

VERİ KAYNAĞI:
- MALIYET_ALICI-1.csv (En iyi 4 alıcının detayları)
- ACILISLAR-1.csv (Güncel Kapanış Fiyatı)

ÇIKTI:
- 1. Alıcının Kim Olduğu ve Maliyeti
- Toplam İlk 4 Alıcının Ortalam Maliyeti
- Fiyat / Maliyet Farkı (%): Negatifse veya 0'a yakınsa alım fırsatıdır.
================================================================================
"""

import pandas as pd
import os
from datetime import datetime

# --- AYARLAR ---
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün"  # CSV dosyalarının okunacağı konum
CIKTI_KONUMU = r"C:\Kullanıcılar\RaporKlasörün"  # CSV raporlarının kaydedileceği konum

# Kurumsal / Yabancı olarak kabul ettiğimiz kurumlar (Örnek Liste)
KURUMSAL_LISTESI = [
    'BANK OF AMERICA', 'CITIBANK', 'DEUTSCHE', 'HSBC', 'YAPI KREDI', 'IS YATIRIM', 'TEB'
]

def kurumsal_maliyet_analizi(ana_dizin):
    print(f"[{ana_dizin}] klasöründeki kurumsal dağılım verileri taranıyor...")
    
    yol_takas = os.path.join(ana_dizin, 'MALIYET_ALICI-1.csv')
    yol_fiyat = os.path.join(ana_dizin, 'ACILISLAR-1.csv')
    
    try:
        # 1. Dosyaları Oku
        df_takas = pd.read_csv(yol_takas)
        df_fiyat = pd.read_csv(yol_fiyat)
        
        sonuclar = []
        
        # Her hisse için tek tek analiz yap
        for index, row in df_takas.iterrows():
            sembol = row['SEMBOL']
            
            # --- 1. ALICI VERİLERİ ---
            alici_1_adi = str(row['ENIYI ALICI.1']).strip()
            alici_1_lot = row['NET ADET']
            alici_1_maliyet = row['MALIYET']
            
            # --- İLK 4 ALICI TOPLAMI (KONSANTRASYON) ---
            # Sütun isimleri: NET ADET, NET ADET.1, NET ADET.2, NET ADET.3
            toplam_net_alim = row['NET ADET'] + row.get('NET ADET.1', 0) + row.get('NET ADET.2', 0) + row.get('NET ADET.3', 0)
            
            # Ağırlıklı Ortalama Maliyet (İlk 4 Kurum)
            # (Maliyet * Lot) toplamı / Toplam Lot
            try:
                toplam_para = (row['NET ADET'] * row['MALIYET']) + \
                              (row.get('NET ADET.1', 0) * row.get('MALIYET.1', 0)) + \
                              (row.get('NET ADET.2', 0) * row.get('MALIYET.2', 0)) + \
                              (row.get('NET ADET.3', 0) * row.get('MALIYET.3', 0))
                
                ort_maliyet_ilk4 = toplam_para / toplam_net_alim if toplam_net_alim != 0 else 0
            except:
                ort_maliyet_ilk4 = 0

            # --- GÜNCEL FİYATI BUL ---
            fiyat_row = df_fiyat[df_fiyat['SEMBOL'] == sembol]
            if not fiyat_row.empty:
                kapanis = fiyat_row.iloc[0]['KAPANIS']
                
                # Fiyat / Maliyet Farkı (%)
                # Eğer %2 ise, kurumun maliyetinin sadece %2 üzerindeyiz (Ucuz).
                fark_yuzde = ((kapanis - alici_1_maliyet) / alici_1_maliyet) * 100 if alici_1_maliyet > 0 else 0
                
                # Kurumsal mı?
                is_institutional = any(k in alici_1_adi.upper() for k in KURUMSAL_LISTESI)
                
                sonuclar.append({
                    'SEMBOL': sembol,
                    'EN_IYI_ALICI': alici_1_adi,
                    'ALICI_KURUMSAL_MI': is_institutional,
                    'ALICI_1_MALIYET': alici_1_maliyet,
                    'ILK4_ORT_MALIYET': ort_maliyet_ilk4,
                    'GUNCEL_FIYAT': kapanis,
                    'MALIYET_FARK_YUZDE': fark_yuzde,
                    'TOPLANAN_LOT': int(toplam_net_alim)
                })
        
        return pd.DataFrame(sonuclar)

    except FileNotFoundError:
        print("HATA: Dosya bulunamadı.")
        return None
    except Exception as e:
        print(f"HATA: {e}")
        return None

# --- ANALİZİ BAŞLAT ---
df_kurumsal = kurumsal_maliyet_analizi(DOSYA_KONUMU)

if df_kurumsal is not None:
    # Çıktı klasörünü kontrol et ve yoksa oluştur
    if not os.path.exists(CIKTI_KONUMU):
        os.makedirs(CIKTI_KONUMU)
        print(f"✓ Çıktı klasörü oluşturuldu: {CIKTI_KONUMU}")
    
    # Zaman damgası
    zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # SENARYO: "Maliyetine Yakın Büyük Toplamalar"
    # 1. Alıcısı "Kurumsal" olsun (BoA, İş vb.)
    # 2. Fiyat, adamların maliyetinden çok uzaklaşmamış olsun (< %5)
    # 3. Yüklü alım olsun
    
    firsat_hisseleri = df_kurumsal[
        (df_kurumsal['ALICI_KURUMSAL_MI'] == True) &
        (df_kurumsal['MALIYET_FARK_YUZDE'] < 5.0) &  # Maliyetten en fazla %5 uzaklaşmış
        (df_kurumsal['MALIYET_FARK_YUZDE'] > -5.0)    # Çok da zararda olmasın (Stop riski)
    ].sort_values(by='TOPLANAN_LOT', ascending=False)
    
    cols = ['SEMBOL', 'EN_IYI_ALICI', 'ALICI_1_MALIYET', 'GUNCEL_FIYAT', 'MALIYET_FARK_YUZDE']
    
    print("\n" + "="*80)
    print(" KURUMSAL ALIM FIRSATLARI (BÜYÜK OYUNCULARIN MALİYETİNE YAKIN HİSSELER)")
    print("="*80)
    
    pd.options.display.float_format = '{:,.2f}'.format
    print(firsat_hisseleri[cols].head(15).to_string(index=False))
    
    # CSV olarak kaydet
    # 1. Tüm Kurumsal Analiz
    tum_dosya = os.path.join(CIKTI_KONUMU, f'KURUMSAL_MALIYET_TUM_{zaman_damgasi}.csv')
    df_kurumsal.to_csv(tum_dosya, index=False, encoding='utf-8-sig')
    print(f"\n✓ Tüm kurumsal maliyet analizi: {tum_dosya}")
    
    # 2. Fırsat Hisseleri (Kurumsal + Maliyete Yakın)
    firsat_dosya = os.path.join(CIKTI_KONUMU, f'KURUMSAL_MALIYET_FIRSAT_{zaman_damgasi}.csv')
    firsat_hisseleri.to_csv(firsat_dosya, index=False, encoding='utf-8-sig')
    print(f"✓ Fırsat hisseleri: {firsat_dosya}")
    
    print("\n[STRATEJİ]: Eğer 'MALIYET_FARK_YUZDE' 0'a yakınsa, BoA/İş Yatırım ile aynı fiyattan maliyetleniyorsun demektir.")
    print("Negatif değerler, kurumun şu an zararda olduğunu ve muhtemelen fiyatı yukarı süreceğini gösterir.")
    
    print("\n" + "="*80)
    print(" ANALİZ TAMAMLANDI - RAPORLAR CSV OLARAK KAYDEDİLDİ")
    print("="*80)