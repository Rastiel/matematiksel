"""
================================================================================
PROJE ADI   : Kademeler Arası Denge Analiz Robotu (Order Book Imbalance Analyzer)
YAZAR       : Borsa (AI Assistant) & Kullanıcı
TARIH       : 2025
VERSIYON    : 1.1

AÇIKLAMA:
Bu script, Borsa İstanbul hisse senetleri için 'Aktif İşlem Dengesi' ve 
'Pasif Emir Dengesi'ni analiz ederek gerçek piyasa yönünü tahmin etmeye çalışır.

GİRDİ DOSYALARI (CSV):
1. KADEME_ANALIZI.csv   -> Gün içi gerçekleşen Alış/Satış işlemleri (Aktif Denge)
2. BEKLEYEN_EMIRLER.csv -> Tahtada bekleyen Alış/Satış emirleri (Pasif Derinlik)

ÇALIŞMA MANTIĞI:
1. Aktif Denge = Gerçekleşen Alışlar - Gerçekleşen Satışlar
2. Pasif Denge = Bekleyen Alış Emirleri - Bekleyen Satış Emirleri
3. Genel Skor  = Aktif Denge + Pasif Denge

ÇIKTI:
- Güçlü Alıcılı Hisseler (Hem aktif alan var, hem tahta dolu) -> YÜKSELİŞ SİNYALİ
- Güçlü Satıcılı Hisseler (Hem aktif satan var, hem tahta satış baskılı) -> DÜŞÜŞ SİNYALİ
================================================================================
"""

import pandas as pd
import os

# --- KULLANICI AYARLARI ---
# CSV dosyalarının bulunduğu klasör yolunu tırnak içine yapıştır.
# Örnek: r"C:\Users\Adiniz\Desktop\BorsaVerileri"
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün" 

def kademe_denge_analizi(ana_dizin):
    print(f"[{ana_dizin}] klasöründeki veriler taranıyor...")
    
    # Dosya yollarını işletim sistemine uygun şekilde oluştur
    yol_kademe = os.path.join(ana_dizin, 'KADEME_ANALIZI.csv')
    yol_bekleyen = os.path.join(ana_dizin, 'BEKLEYEN_EMIRLER.csv')
    
    try:
        # 1. Dosyaları Oku
        df_kademe = pd.read_csv(yol_kademe)
        df_bekleyen = pd.read_csv(yol_bekleyen)
        
        # 2. Sütunları Seç ve Standartlaştır
        # FARK: Aktif Alıcıların Satıcılara üstünlüğü
        df_active = df_kademe[['SEMBOL', 'FARK']].rename(columns={'FARK': 'AKTIF_DENGE'})
        
        # NET.EMIR.FARKI: Tahtadaki pasif alıcıların satıcılara üstünlüğü
        df_passive = df_bekleyen[['SEMBOL', 'NET.EMIR.FARKI']].rename(columns={'NET.EMIR.FARKI': 'PASIF_DENGE'})
        
        # 3. İki tabloyu SEMBOL üzerinden birleştir
        df_merged = pd.merge(df_active, df_passive, on='SEMBOL', how='inner')
        
        # 4. Genel Denge Puanını Hesapla
        df_merged['GENEL_DENGE'] = df_merged['AKTIF_DENGE'] + df_merged['PASIF_DENGE']
        
        return df_merged

    except FileNotFoundError:
        print("\n!!! HATA: Belirtilen klasörde dosyalar bulunamadı.")
        print("Lütfen 'DOSYA_KONUMU' satırındaki yolu ve dosya isimlerini kontrol et.")
        return None
    except Exception as e:
        print(f"\n!!! BEKLENMEDİK HATA: {e}")
        return None

# --- ANA PROGRAM ---

analiz_sonucu = kademe_denge_analizi(DOSYA_KONUMU)

if analiz_sonucu is not None:
    # SENARYO 1: BOĞA PİYASASI ADAYLARI (Güçlü Alış İsteği)
    # Hem anlık alıyorlar, hem de alta alış yazıp destekliyorlar.
    guclu_alicili = analiz_sonucu[
        (analiz_sonucu['AKTIF_DENGE'] > 0) & 
        (analiz_sonucu['PASIF_DENGE'] > 0)
    ].sort_values(by='GENEL_DENGE', ascending=False)
    
    # SENARYO 2: AYI PİYASASI ADAYLARI (Güçlü Satış Baskısı)
    # Hem anlık satıyorlar, hem de üste satış yazıp baskılıyorlar.
    guclu_saticili = analiz_sonucu[
        (analiz_sonucu['AKTIF_DENGE'] < 0) & 
        (analiz_sonucu['PASIF_DENGE'] < 0)
    ].sort_values(by='GENEL_DENGE', ascending=True)

    print("\n" + "="*50)
    print(" GÜÇLÜ ALICILI HİSSELER (TOP 10) - YÜKSELİŞ ADAYI")
    print("="*50)
    print(guclu_alicili[['SEMBOL', 'AKTIF_DENGE', 'PASIF_DENGE', 'GENEL_DENGE']].head(10).to_string(index=False))
    
    print("\n" + "="*50)
    print(" GÜÇLÜ SATICILI HİSSELER (TOP 10) - DÜŞÜŞ ADAYI")
    print("="*50)
    print(guclu_saticili[['SEMBOL', 'AKTIF_DENGE', 'PASIF_DENGE', 'GENEL_DENGE']].head(10).to_string(index=False))
    
    print("\nAnaliz tamamlandı.")