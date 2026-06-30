import os
import pandas as pd
import requests
import io
from typing import Dict

# Pre-compiled fallback dictionary containing 70+ popular liquid tickers.
# Used if the app is offline or GitHub connection fails on the first run.
IDX_FALLBACK_STOCKS = {
    "BBCA.JK": "Bank Central Asia Tbk.",
    "BBRI.JK": "Bank Rakyat Indonesia (Persero) Tbk.",
    "BMRI.JK": "Bank Mandiri (Persero) Tbk.",
    "BBNI.JK": "Bank Negara Indonesia (Persero) Tbk.",
    "TLKM.JK": "Telkom Indonesia (Persero) Tbk.",
    "ASII.JK": "Astra International Tbk.",
    "UNVR.JK": "Unilever Indonesia Tbk.",
    "ICBP.JK": "Indofood CBP Sukses Makmur Tbk.",
    "INDF.JK": "Indofood Sukses Makmur Tbk.",
    "GOTO.JK": "GoTo Gojek Tokopedia Tbk.",
    "ADRO.JK": "Adaro Energy Indonesia Tbk.",
    "MDKA.JK": "Merdeka Copper Gold Tbk.",
    "ANTM.JK": "Aneka Tambang Tbk.",
    "PGAS.JK": "Perusahaan Gas Negara Tbk.",
    "KLBF.JK": "Kalbe Farma Tbk.",
    "CPIN.JK": "Charoen Pokphand Indonesia Tbk.",
    "AMRT.JK": "Sumber Alfaria Trijaya Tbk. (Alfamart)",
    "BRMS.JK": "Bumi Resources Minerals Tbk.",
    "BRPT.JK": "Barito Pacific Tbk.",
    "TPIA.JK": "Chandra Asri Petrochemical Tbk.",
    "BREN.JK": "Barito Renewables Energy Tbk.",
    "CUAN.JK": "Petrindo Jaya Kreasi Tbk.",
    "INCO.JK": "Vale Indonesia Tbk.",
    "PTBA.JK": "Bukit Asam Tbk.",
    "ITMG.JK": "Indo Tambangraya Megah Tbk.",
    "HRUM.JK": "Harum Energy Tbk.",
    "UNTR.JK": "United Tractors Tbk.",
    "MYOR.JK": "Mayora Indah Tbk.",
    "GGRM.JK": "Gudang Garam Tbk.",
    "HMSP.JK": "H.M. Sampoerna Tbk.",
    "EXCL.JK": "XL Axiata Tbk.",
    "ISAT.JK": "Indosat Ooredoo Hutchison Tbk.",
    "TOWR.JK": "Sarana Menara Nusantara Tbk.",
    "TBIG.JK": "Tower Bersama Infrastructure Tbk.",
    "MEDC.JK": "Medco Energi Internasional Tbk.",
    "AKRA.JK": "AKR Corporindo Tbk.",
    "JSMR.JK": "Jasa Marga (Persero) Tbk.",
    "SMGR.JK": "Semen Indonesia (Persero) Tbk.",
    "INTP.JK": "Indocement Tunggal Prakarsa Tbk.",
    "ADMR.JK": "Adaro Minerals Indonesia Tbk.",
    "ARTO.JK": "Bank Jago Tbk.",
    "BUMI.JK": "Bumi Resources Tbk.",
    "BBTN.JK": "Bank Tabungan Negara (Persero) Tbk.",
    "PNLF.JK": "Panin Financial Tbk.",
    "BSDE.JK": "Bumi Serpong Damai Tbk.",
    "PWON.JK": "Pakuwon Jati Tbk.",
    "CTRA.JK": "Ciputra Development Tbk.",
    "SMRA.JK": "Summarecon Agung Tbk.",
    "WIKA.JK": "Wijaya Karya (Persero) Tbk.",
    "PTPP.JK": "PP (Persero) Tbk.",
    "ADHI.JK": "Adhi Karya (Persero) Tbk.",
    "SSMS.JK": "Sawit Sumbermas Sarana Tbk.",
    "LSIP.JK": "London Sumatra Indonesia Tbk.",
    "AALI.JK": "Astra Agro Lestari Tbk.",
    "DSNG.JK": "Dharma Satya Nusantara Tbk.",
    "SIDO.JK": "Industri Jamu dan Farmasi Sido Muncul Tbk.",
    "ACES.JK": "Aspirasi Hidup Indonesia Tbk. (Ace Hardware)",
    "MAPI.JK": "Mitra Adiperkasa Tbk.",
    "ERAA.JK": "Erajaya Swasembada Tbk.",
    "BIRD.JK": "Blue Bird Tbk.",
    "MBMA.JK": "Merdeka Battery Materials Tbk.",
    "NCKL.JK": "Trimegah Bangun Persada Tbk. (Harita Nickel)",
    "HEAL.JK": "Medikaloka Hermina Tbk. (RS Hermina)",
    "MIKA.JK": "Mitra Keluarga Karyasehat Tbk.",
    "SILO.JK": "Siloam International Hospitals Tbk.",
    "BUKA.JK": "Bukalapak.com Tbk.",
    "SCMA.JK": "Surya Citra Media Tbk.",
    "MNCN.JK": "Media Nusantara Citra Tbk.",
    "AUTO.JK": "Astra Otoparts Tbk.",
    "IMAS.JK": "Indomobil Sukses Internasional Tbk."
}

CACHE_FILE_PATH = "data/all_idx_stocks.csv"

def get_all_idx_tickers() -> Dict[str, str]:
    """
    Returns a dictionary of all IDX stock tickers and their company names.
    Tries to load from a local cache file first. If it doesn't exist, it pulls
    listings from GitHub, caches it, and falls back to a static list if offline.
    """
    # 1. Read from local cache file if exists
    if os.path.exists(CACHE_FILE_PATH):
        try:
            df = pd.read_csv(CACHE_FILE_PATH)
            # Convert back to dictionary
            return dict(zip(df['ticker'], df['name']))
        except Exception as e:
            print(f"Error reading stock list cache: {e}")

    # 2. Try fetching from wildangunawan/Dataset-Saham-IDX on GitHub
    SECTORS = [
        "Energy.csv",
        "Basic Materials.csv",
        "Industrials.csv",
        "Consumer Non-Cyclicals.csv",
        "Consumer Cyclicals.csv",
        "Healthcare.csv",
        "Financials.csv",
        "Properties & Real Estate.csv",
        "Technology.csv",
        "Infrastructures.csv",
        "Transportation & Logistic.csv"
    ]
    
    all_stocks = {}
    
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        session = requests.Session()
        session.verify = False
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        })
        
        print("Downloading all stock tickers from GitHub...")
        for sector in SECTORS:
            url = f"https://raw.githubusercontent.com/wildangunawan/Dataset-Saham-IDX/master/List%20Emiten/Sectors/{sector.replace(' ', '%20').replace('&', '%26')}"
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                df_sector = pd.read_csv(io.StringIO(response.text))
                for _, row in df_sector.iterrows():
                    code = f"{row['code']}.JK"
                    all_stocks[code] = row['name']
                    
        if all_stocks:
            # Save to cache file
            os.makedirs(os.path.dirname(CACHE_FILE_PATH) or '.', exist_ok=True)
            df_cache = pd.DataFrame(list(all_stocks.items()), columns=['ticker', 'name'])
            df_cache.to_csv(CACHE_FILE_PATH, index=False)
            print(f"Successfully cached {len(all_stocks)} stocks locally.")
            return all_stocks
            
    except Exception as e:
        print(f"Failed to fetch stock list dynamically: {e}. Falling back to pre-compiled list.")
        
    # 3. Fallback to pre-compiled popular stocks list if offline
    return IDX_FALLBACK_STOCKS
