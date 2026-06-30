import pandas as pd
import yfinance as yf
from typing import Dict, Optional, List

class StockDataLoader:
    """
    Interface/Class to load stock data.
    Can be easily swapped with official IDX API, delayed data feed, or other data providers.
    """
    def __init__(self):
        import requests
        import urllib3
        # Disable SSL warnings for self-signed certificates
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.session = requests.Session()
        self.session.verify = False
        # Set a browser User-Agent to prevent Yahoo Rate Limiting
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        })


    def fetch_historical_data(self, ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        Fetch historical stock data.
        Returns a pandas DataFrame with columns: Date, Open, High, Low, Close, Volume.
        """
        try:
            # yfinance fetch with custom session
            stock = yf.Ticker(ticker, session=self.session)
            df = stock.history(period=period)
            if df.empty:
                return None
            
            # Clean up index and ensure standard columns exist
            df = df.reset_index()
            
            # Standardize date column
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
            elif 'Datetime' in df.columns:
                df['Date'] = pd.to_datetime(df['Datetime']).dt.tz_localize(None)
            
            # Rename columns to standard casing
            rename_map = {}
            for col in df.columns:
                if col.lower() in ['open', 'high', 'low', 'close', 'volume']:
                    rename_map[col] = col.capitalize()
            if rename_map:
                df = df.rename(columns=rename_map)
                
            required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            # Check if all required columns are present
            if not all(col in df.columns for col in required_cols):
                return None
                
            df = df[required_cols].copy()
            return df
        except Exception as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
            return None

    def fetch_latest_quote(self, ticker: str) -> Dict:
        """
        Fetch the latest quote details for a ticker.
        """
        try:
            stock = yf.Ticker(ticker, session=self.session)
            # Fetch fast info or history to get the latest close price and volume safely
            # yf.Ticker.info can be slow or fail, history is more reliable
            df = stock.history(period="5d")
            if not df.empty:
                last_row = df.iloc[-1]
                prev_row = df.iloc[-2] if len(df) > 1 else last_row
                return {
                    "ticker": ticker,
                    "name": stock.info.get("longName", ticker.replace(".JK", "")),
                    "currentPrice": float(last_row['Close']),
                    "open": float(last_row['Open']),
                    "dayHigh": float(last_row['High']),
                    "dayLow": float(last_row['Low']),
                    "volume": int(last_row['Volume']),
                    "previousClose": float(prev_row['Close'])
                }
            return {}
        except Exception as e:
            print(f"Error fetching quote for {ticker}: {str(e)}")
            return {}
