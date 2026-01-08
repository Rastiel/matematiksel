"""
================================================================================
PROJE ADI   : Açılış İştahı ve Gap Analizi
YAZAR       : Borsa (AI Assistant)
VERSIYON    : 2.0 (CSV Çıktılı)

AÇIKLAMA:
Bu script, hisselerin güne nasıl başladığını analiz eder.
Özellikle 'Gapli Açılışları' (Önceki kapanıştan farklı açılış) ve 
bu açılışın devamının gelip gelmediğini kontrol eder.

SİNYALLER:
- GÜÇLÜ İŞTAH: Gapli yukarı açılış + Yükselişin devamı (Alım Fırsatı).
- TUZAK AÇILIŞ: Gapli yukarı açılış + Sert düşüş (Satış/Uzak Dur Sinyali).

YENİ ÖZELLİKLER:
- Sonuçlar artık CSV formatında kaydediliyor
- İki ayrı CSV dosyası oluşturuluyor: Güçlü İştah ve Tuzak Açılışlar
================================================================================
"""

import pandas as pd
import os
from datetime import datetime

# --- AYARLAR ---
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün"  # CSV dosyalarının okunacağı konum
CIKTI_KONUMU = r"C:\Kullanıcılar\RaporKlasörün"  # CSV raporlarının kaydedileceği konum 

def acilis_istahi_analizi(ana_dizin):
    print(f"[{ana_dizin}] klasöründeki verilerle Açılış İştahı analizi yapılıyor...")
    
    yol_fiyat = os.path.join(ana_dizin, 'ACILISLAR-1.csv')
    
    try:
        if os.path.exists(yol_fiyat):
            df = pd.read_csv(yol_fiyat)
        else:
            print(f"HATA: {yol_fiyat} dosyası bulunamadı!")
            return None
        
        # HESAPLAMALAR
        # 1. GAP (Boşluk): Açılış - Önceki Kapanış
        if 'KAPANIS-1' in df.columns:
            df['GAP_YUZDE'] = ((df['ACILIS'] - df['KAPANIS-1']) / df['KAPANIS-1']) * 100
        else:
            df['GAP_YUZDE'] = 0
            
        # 2. PERFORMANS: Şu Anki Fiyat - Açılış Fiyatı
        df['ACILIS_PERFORMANSI_YUZDE'] = ((df['KAPANIS'] - df['ACILIS']) / df['ACILIS']) * 100
        
        # 3. İŞTAH SKORU
        df['ISTAH_PUANI'] = df['GAP_YUZDE'] + df['ACILIS_PERFORMANSI_YUZDE']
        
        return df

    except Exception as e:
        print(f"HATA: {e}")
        return None

# --- RAPORLAMA VE CSV KAYDETME ---
df_istah = acilis_istahi_analizi(DOSYA_KONUMU)

if df_istah is not None:
    # Çıktı klasörünü kontrol et ve yoksa oluştur
    if not os.path.exists(CIKTI_KONUMU):
        os.makedirs(CIKTI_KONUMU)
        print(f"✓ Çıktı klasörü oluşturuldu: {CIKTI_KONUMU}")
    
    # Zaman damgası ekle (dosya adı için)
    zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. GÜÇLÜ AÇILIŞ YAPANLAR
    guclu = df_istah[
        (df_istah['GAP_YUZDE'] > 0.5) & 
        (df_istah['ACILIS_PERFORMANSI_YUZDE'] > 0.5)
    ].sort_values(by='ISTAH_PUANI', ascending=False).head(10)
    
    # Konsola yazdır
    print("\n" + "="*85)
    print(" GÜÇLÜ İŞTAH (GAPLI AÇILIŞ + YÜKSELİŞ DEVAM EDİYOR)")
    print("="*85)
    print(guclu[['SEMBOL', 'ACILIS', 'KAPANIS', 'GAP_YUZDE', 'ACILIS_PERFORMANSI_YUZDE']].to_string(index=False))
    
    # CSV olarak kaydet
    guclu_dosya = os.path.join(CIKTI_KONUMU, f'GUCLU_ISTAH_{zaman_damgasi}.csv')
    guclu[['SEMBOL', 'ACILIS', 'KAPANIS', 'GAP_YUZDE', 'ACILIS_PERFORMANSI_YUZDE', 'ISTAH_PUANI']].to_csv(
        guclu_dosya, 
        index=False, 
        encoding='utf-8-sig'  # Türkçe karakterler için
    )
    print(f"\n✓ Güçlü İştah raporu kaydedildi: {guclu_dosya}")
    
    # 2. TUZAK AÇILIŞLAR
    tuzak = df_istah[
        (df_istah['GAP_YUZDE'] > 1.0) & 
        (df_istah['ACILIS_PERFORMANSI_YUZDE'] < -0.5)
    ].sort_values(by='ACILIS_PERFORMANSI_YUZDE', ascending=True).head(10)
    
    # Konsola yazdır
    print("\n" + "="*85)
    print(" AÇILIŞ TUZAĞI (YÜKSEK AÇIP DÜŞENLER - DİKKAT!)")
    print("="*85)
    print(tuzak[['SEMBOL', 'ACILIS', 'KAPANIS', 'GAP_YUZDE', 'ACILIS_PERFORMANSI_YUZDE']].to_string(index=False))
    
    # CSV olarak kaydet
    tuzak_dosya = os.path.join(CIKTI_KONUMU, f'TUZAK_ACILIS_{zaman_damgasi}.csv')
    tuzak[['SEMBOL', 'ACILIS', 'KAPANIS', 'GAP_YUZDE', 'ACILIS_PERFORMANSI_YUZDE', 'ISTAH_PUANI']].to_csv(
        tuzak_dosya, 
        index=False, 
        encoding='utf-8-sig'
    )
    print(f"✓ Tuzak Açılış raporu kaydedildi: {tuzak_dosya}")
    
    # 3. TÜM ANALİZ SONUÇLARI (BONUS)
    tum_analiz_dosya = os.path.join(CIKTI_KONUMU, f'TUM_ACILIS_ANALIZI_{zaman_damgasi}.csv')
    df_istah.to_csv(tum_analiz_dosya, index=False, encoding='utf-8-sig')
    print(f"✓ Tüm analiz sonuçları kaydedildi: {tum_analiz_dosya}")
    
    print("\n" + "="*85)
    print(" ANALİZ TAMAMLANDI - TÜM RAPORLAR CSV OLARAK KAYDEDİLDİ")
    print("="*85)
else:
    print("\nAnaliz yapılamadı. Lütfen dosya yolunu ve CSV formatını kontrol edin.")