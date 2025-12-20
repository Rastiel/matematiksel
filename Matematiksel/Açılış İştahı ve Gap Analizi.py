"""
================================================================================
PROJE ADI   : Açılış İştahı ve Gap Analizi
YAZAR       : Borsa (AI Assistant)
VERSIYON    : 1.0

AÇIKLAMA:
Bu script, hisselerin güne nasıl başladığını analiz eder.
Özellikle 'Gapli Açılışları' (Önceki kapanıştan farklı açılış) ve 
bu açılışın devamının gelip gelmediğini kontrol eder.

SİNYALLER:
- GÜÇLÜ İŞTAH: Gapli yukarı açılış + Yükselişin devamı (Alım Fırsatı).
- TUZAK AÇILIŞ: Gapli yukarı açılış + Sert düşüş (Satış/Uzak Dur Sinyali).
================================================================================
"""

import pandas as pd
import os

# --- AYARLAR ---
DOSYA_KONUMU = r"C:\Kullanıcılar\SeninKlasörün" 

def acilis_istahi_analizi(ana_dizin):
    print(f"[{ana_dizin}] klasöründeki verilerle Açılış İştahı analizi yapılıyor...")
    
    yol_fiyat = os.path.join(ana_dizin, 'ACILISLAR-1.csv')
    
    try:
        if os.path.exists(yol_fiyat):
            df = pd.read_csv(yol_fiyat)
        else:
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

# --- RAPORLAMA ---
df_istah = acilis_istahi_analizi(DOSYA_KONUMU)

if df_istah is not None:
    # 1. GÜÇLÜ AÇILIŞ YAPANLAR
    guclu = df_istah[
        (df_istah['GAP_YUZDE'] > 0.5) & 
        (df_istah['ACILIS_PERFORMANSI_YUZDE'] > 0.5)
    ].sort_values(by='ISTAH_PUANI', ascending=False).head(10)
    
    print("\n" + "="*85)
    print(" GÜÇLÜ İŞTAH (GAPLI AÇILIŞ + YÜKSELİŞ DEVAM EDİYOR)")
    print("="*85)
    print(guclu[['SEMBOL', 'ACILIS', 'KAPANIS', 'GAP_YUZDE', 'ACILIS_PERFORMANSI_YUZDE']].to_string(index=False))
    
    # 2. TUZAK AÇILIŞLAR
    tuzak = df_istah[
        (df_istah['GAP_YUZDE'] > 1.0) & 
        (df_istah['ACILIS_PERFORMANSI_YUZDE'] < -0.5)
    ].sort_values(by='ACILIS_PERFORMANSI_YUZDE', ascending=True).head(10)
    
    print("\n" + "="*85)
    print(" AÇILIŞ TUZAĞI (YÜKSEK AÇIP DÜŞENLER - DİKKAT!)")
    print("="*85)
    print(tuzak[['SEMBOL', 'ACILIS', 'KAPANIS', 'GAP_YUZDE', 'ACILIS_PERFORMANSI_YUZDE']].to_string(index=False))