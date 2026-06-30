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

def get_idx_stocks_df() -> pd.DataFrame:
    """
    Returns a pandas DataFrame of all IDX stocks with columns: ticker, name, sector.
    Uses local cache if available, otherwise downloads from GitHub.
    """
    # 1. Read from local cache file if exists
    if os.path.exists(CACHE_FILE_PATH):
        try:
            df = pd.read_csv(CACHE_FILE_PATH)
            if 'sector' in df.columns:
                return df
        except Exception as e:
            print(f"Error reading stock list cache: {e}")

    # 2. Try fetching from wildangunawan/Dataset-Saham-IDX on GitHub
    SECTORS = {
        "Energy": "Energy.csv",
        "Basic Materials": "Basic Materials.csv",
        "Industrials": "Industrials.csv",
        "Consumer Non-Cyclical": "Consumer Non-Cyclicals.csv",
        "Consumer Cyclical": "Consumer Cyclicals.csv",
        "Healthcare": "Healthcare.csv",
        "Financials": "Financials.csv",
        "Properties & Real Estate": "Properties & Real Estate.csv",
        "Technology": "Technology.csv",
        "Infrastructure": "Infrastructures.csv",
        "Transportation & Logistics": "Transportation & Logistic.csv"
    }
    
    rows = []
    
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
        for sector_name, filename in SECTORS.items():
            url = f"https://raw.githubusercontent.com/wildangunawan/Dataset-Saham-IDX/master/List%20Emiten/Sectors/{filename.replace(' ', '%20').replace('&', '%26')}"
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                df_sector = pd.read_csv(io.StringIO(response.text))
                for _, row in df_sector.iterrows():
                    rows.append({
                        "ticker": f"{row['code']}.JK",
                        "name": row['name'],
                        "sector": sector_name
                    })
                    
        if rows:
            df_cache = pd.DataFrame(rows)
            # Save to cache file
            os.makedirs(os.path.dirname(CACHE_FILE_PATH) or '.', exist_ok=True)
            df_cache.to_csv(CACHE_FILE_PATH, index=False)
            print(f"Successfully cached {len(df_cache)} stocks locally.")
            return df_cache
            
    except Exception as e:
        print(f"Failed to fetch stock list dynamically: {e}")
        
    # 3. Fallback to precompiled list if offline
    fallback_rows = []
    for ticker, name in IDX_FALLBACK_STOCKS.items():
        # Guestimate sector
        if ticker in ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BBTN.JK", "ARTO.JK", "PNLF.JK"]:
            sector = "Financials"
        elif ticker in ["TLKM.JK", "EXCL.JK", "ISAT.JK", "TOWR.JK", "TBIG.JK"]:
            sector = "Infrastructure"
        elif ticker in ["ADRO.JK", "PTBA.JK", "ITMG.JK", "HRUM.JK", "MEDC.JK", "BUMI.JK", "ADMR.JK"]:
            sector = "Energy"
        elif ticker in ["MDKA.JK", "ANTM.JK", "INCO.JK", "BRMS.JK", "NCKL.JK", "MBMA.JK"]:
            sector = "Basic Materials"
        else:
            sector = "Other / Diversified"
            
        fallback_rows.append({
            "ticker": ticker,
            "name": name,
            "sector": sector
        })
    return pd.DataFrame(fallback_rows)

def get_all_idx_tickers() -> Dict[str, str]:
    """
    Backwards compatibility: Returns a dictionary of all IDX stock tickers and their company names.
    """
    df = get_idx_stocks_df()
    return dict(zip(df['ticker'], df['name']))
