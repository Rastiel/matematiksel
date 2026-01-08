"""
================================================================================
PROJE ADI   : Tahtacı Manipülasyon Tespit Modeli (Market Maker Signals)
YAZAR       : Borsa (AI Assistant)
VERSIYON    : 1.7 (CSV Çıktılı)

AÇIKLAMA:
Bu script, fiyat, hacim, aktif akış ve pasif derinlik verilerini çaprazlayarak
büyük oyuncuların kurduğu tuzakları tespit eder.

SINYALLER:
1. WASH TRADING (Hacim Var, Hareket Yok): Yatay piyasada yapay hacim.
2. FAKE BUY WALL (Sahte Destek): Altta yastık var ama aktif satış yeniyor. (Düşüş habercisi)
3. SUPPRESSION (Baskılama): Üstte duvar var ama aktif alım yapılıyor. (Patlama habercisi)
================================================================================
"""

import pandas as pd
import os
from datetime import datetime

# --- AYARLAR ---
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün"  # CSV dosyalarının okunacağı konum
CIKTI_KONUMU = r"C:\Kullanıcılar\RaporKlasörün"  # CSV raporlarının kaydedileceği konum

def manipulasyon_analizi(ana_dizin):
    print(f"[{ana_dizin}] üzerinde manipülasyon taraması yapılıyor...")
    
    yol_fiyat = os.path.join(ana_dizin, 'ACILISLAR-1.csv')
    yol_kademe = os.path.join(ana_dizin, 'KADEME_ANALIZI.csv')
    yol_bekleyen = os.path.join(ana_dizin, 'BEKLEYEN_EMIRLER.csv')
    
    try:
        # Dosyaları Oku
        df_fiyat = pd.read_csv(yol_fiyat)
        df_kademe = pd.read_csv(yol_kademe)
        df_bekleyen = pd.read_csv(yol_bekleyen)
        
        # --- 1. HACİM VE FİYAT VERİLERİ ---
        # Rölatif Hacim (Son 5 gün ortalamasına göre bugünkü durum)
        hacim_cols = [f'HACIM-{i}' for i in range(1, 6)]
        if all(c in df_fiyat.columns for c in hacim_cols):
            df_fiyat['ORT_HACIM_5G'] = df_fiyat[hacim_cols].mean(axis=1)
            df_fiyat['ROLATIF_HACIM'] = df_fiyat['HACIM'] / df_fiyat['ORT_HACIM_5G']
        else:
             df_fiyat['ROLATIF_HACIM'] = 1.0 
             
        df_fiyat['DEGISIM_YUZDE'] = ((df_fiyat['KAPANIS'] - df_fiyat['KAPANIS-1']) / df_fiyat['KAPANIS-1']) * 100
        
        # --- 2. AKTİF VE PASİF VERİLERİ ---
        # Aktif Net: Anlık gerçekleşen işlemlerde kim baskın?
        df_kademe = df_kademe[['SEMBOL', 'FARK']].rename(columns={'FARK': 'AKTIF_NET_LOT'})
        
        # Pasif Net: Bekleyen emirlerde kim baskın?
        df_bekleyen = df_bekleyen[['SEMBOL', 'NET.EMIR.FARKI']].rename(columns={'NET.EMIR.FARKI': 'PASIF_NET_LOT'})
        
        # Birleştirme
        df_m = pd.merge(df_fiyat, df_kademe, on='SEMBOL', how='inner')
        df_m = pd.merge(df_m, df_bekleyen, on='SEMBOL', how='inner')
        
        # --- 3. MANİPÜLASYON SENARYOLARI ---
        
        # SENARYO A: "WASH TRADING" (Hacim Var, İcraat Yok)
        # Hacim çok yüksek (>2 kat), ama fiyat değişimi çok küçük (<%0.5).
        # Amaç: Hissede hareket varmış gibi gösterip ky çekmek.
        df_m['SINYAL_WASH'] = (df_m['ROLATIF_HACIM'] > 2.0) & (df_m['DEGISIM_YUZDE'].abs() < 0.5)
        
        # SENARYO B: "SAHTE DESTEK / MAL ÇAKMA" (Boğa Tuzağı)
        # Görüntü: Altta çok alıcı bekliyor (Pasif > 0), güvenli liman gibi.
        # Gerçek: Aktif olarak satış yeniyor (Aktif < 0).
        # Anlamı: Tahtacı alta kendi alışlarını yazıp "Düşmez bu" diyor, ama yukarıdan malı veriyor.
        df_m['SINYAL_SAHTE_DESTEK'] = (df_m['PASIF_NET_LOT'] > 0) & (df_m['AKTIF_NET_LOT'] < 0) & (df_m['DEGISIM_YUZDE'] > -2.0)
        
        # SENARYO C: "BASKILAMA / MAL TOPLAMA" (Ayı Tuzağı)
        # Görüntü: Üstte çok satıcı var (Pasif < 0), gitmez bu hisse gibi.
        # Gerçek: Aktif olarak alım yapılıyor (Aktif > 0).
        # Anlamı: Tahtacı üste duvar örüp fiyatı tutuyor, alttan dökülenleri topluyor.
        df_m['SINYAL_BASKILAMA'] = (df_m['PASIF_NET_LOT'] < 0) & (df_m['AKTIF_NET_LOT'] > 0)
        
        # Filtreleme
        supheli_hisseler = df_m[df_m['SINYAL_WASH'] | df_m['SINYAL_SAHTE_DESTEK'] | df_m['SINYAL_BASKILAMA']].copy()
        
        # Etiketleme Fonksiyonu
        def etiketle(row):
            tespitler = []
            if row['SINYAL_WASH']: tespitler.append("HACIM VAR YON YOK (Fake Hacim)")
            if row['SINYAL_SAHTE_DESTEK']: tespitler.append("SAHTE DESTEK (Mal Cakma)")
            if row['SINYAL_BASKILAMA']: tespitler.append("BASKILAMA (Mal Toplama)")
            return " + ".join(tespitler)
            
        supheli_hisseler['MANIPULASYON_TURU'] = supheli_hisseler.apply(etiketle, axis=1)
        
        return supheli_hisseler[['SEMBOL', 'KAPANIS', 'DEGISIM_YUZDE', 'ROLATIF_HACIM', 'AKTIF_NET_LOT', 'PASIF_NET_LOT', 'MANIPULASYON_TURU']]

    except FileNotFoundError:
        print("HATA: Dosya bulunamadı.")
        return None
    except Exception as e:
        print(f"HATA: {e}")
        return None

# --- ANALİZİ BAŞLAT ---
df_sonuc = manipulasyon_analizi(DOSYA_KONUMU)

if df_sonuc is not None:
    # Çıktı klasörünü kontrol et ve yoksa oluştur
    if not os.path.exists(CIKTI_KONUMU):
        os.makedirs(CIKTI_KONUMU)
        print(f"✓ Çıktı klasörü oluşturuldu: {CIKTI_KONUMU}")
    
    # Zaman damgası
    zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. BASKILANANLAR (TOPLANANLAR) - Yükseliş Adayı
    toplananlar = df_sonuc[df_sonuc['MANIPULASYON_TURU'].str.contains("BASKILAMA")].sort_values(by='AKTIF_NET_LOT', ascending=False)
    
    print("\n" + "="*85)
    print(" GİZLİCE TOPLANAN HİSSELER (BASKILAMA VAR - POZİTİF SİNYAL)")
    print("="*85)
    print(toplananlar.head(10).to_string(index=False))
    
    # 2. SAHTE DESTEKLİLER (MAL ÇAKILANLAR) - Düşüş Adayı
    cakilanlar = df_sonuc[df_sonuc['MANIPULASYON_TURU'].str.contains("SAHTE DESTEK")].sort_values(by='AKTIF_NET_LOT', ascending=True) # En çok satılan en üstte
    
    print("\n" + "="*85)
    print(" DİKKAT! TUZAK OLABİLİR (SAHTE DESTEK - NEGATİF SİNYAL)")
    print("="*85)
    print(cakilanlar.head(10).to_string(index=False))

    # CSV olarak kaydet
    # 1. Tüm Şüpheli Hisseler
    tum_dosya = os.path.join(CIKTI_KONUMU, f'MANIPULASYON_TUM_{zaman_damgasi}.csv')
    df_sonuc.to_csv(tum_dosya, index=False, encoding='utf-8-sig')
    print(f"\n✓ Tüm manipülasyon tespitleri: {tum_dosya}")
    
    # 2. Baskılananlar (Toplananlar)
    toplanan_dosya = os.path.join(CIKTI_KONUMU, f'MANIPULASYON_BASKILAMA_{zaman_damgasi}.csv')
    toplananlar.to_csv(toplanan_dosya, index=False, encoding='utf-8-sig')
    print(f"✓ Baskılama tespitleri: {toplanan_dosya}")
    
    # 3. Sahte Destekler
    sahte_dosya = os.path.join(CIKTI_KONUMU, f'MANIPULASYON_SAHTE_DESTEK_{zaman_damgasi}.csv')
    cakilanlar.to_csv(sahte_dosya, index=False, encoding='utf-8-sig')
    print(f"✓ Sahte destek tespitleri: {sahte_dosya}")

    print("\n[İPUCU]: 'BASKILAMA' tespit edilen hisselerde, yukarıdaki 'Satış Duvarı' kaldırıldığı an sert yükseliş başlayabilir.")
    
    print("\n" + "="*85)
    print(" ANALİZ TAMAMLANDI - RAPORLAR CSV OLARAK KAYDEDİLDİ")
    print("="*85)