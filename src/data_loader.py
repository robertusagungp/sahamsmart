import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import random
from typing import Dict, Optional, List

class StockDataLoader:
    """
    Interface/Class to load stock data.
    Can be easily swapped with official IDX API, delayed data feed, or other data providers.
    Supports local CSV data files for Broker Summary and Foreign Flow in prototype mode.
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
        
        # CSV File Paths
        self.broker_csv_path = "data/sample_broker_summary.csv"
        self.foreign_csv_path = "data/sample_foreign_flow.csv"
        
        # Generate sample datasets if they do not exist
        self._ensure_sample_files_exist()

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

    # ================= BANDARMOLOGI & FLOW LOADER METHODS =================

    def fetch_broker_summary(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Fetch broker summary details for a ticker from the CSV file.
        """
        if not os.path.exists(self.broker_csv_path):
            return None
        try:
            df = pd.read_csv(self.broker_csv_path)
            df['date'] = pd.to_datetime(df['date']).dt.date
            # Filter by ticker
            df_ticker = df[df['ticker'] == ticker].copy()
            if df_ticker.empty:
                # If ticker is missing in sample, generate dynamically
                self._generate_mock_data_for_ticker(ticker)
                # Re-read
                df = pd.read_csv(self.broker_csv_path)
                df['date'] = pd.to_datetime(df['date']).dt.date
                df_ticker = df[df['ticker'] == ticker].copy()
            return df_ticker
        except Exception as e:
            print(f"Error reading broker summary: {e}")
            return None

    def fetch_foreign_flow(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Fetch foreign flow details for a ticker from the CSV file.
        """
        if not os.path.exists(self.foreign_csv_path):
            return None
        try:
            df = pd.read_csv(self.foreign_csv_path)
            df['date'] = pd.to_datetime(df['date']).dt.date
            # Filter by ticker
            df_ticker = df[df['ticker'] == ticker].copy()
            if df_ticker.empty:
                # If ticker is missing in sample, generate dynamically
                self._generate_mock_data_for_ticker(ticker)
                # Re-read
                df = pd.read_csv(self.foreign_csv_path)
                df['date'] = pd.to_datetime(df['date']).dt.date
                df_ticker = df[df['ticker'] == ticker].copy()
            return df_ticker
        except Exception as e:
            print(f"Error reading foreign flow: {e}")
            return None

    # ================= GENERATION OF PROTOTYPE MOCK DATA =================

    def _ensure_sample_files_exist(self):
        """Generates sample broker and foreign flow CSV files if they don't exist."""
        os.makedirs("data", exist_ok=True)
        
        # Check files
        if not os.path.exists(self.broker_csv_path) or not os.path.exists(self.foreign_csv_path):
            print("Generating prototype bandarmologi sample files...")
            default_tickers = ["BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK", "UNVR.JK", "GOTO.JK", "ADRO.JK", "MDKA.JK"]
            
            # Reset/Initialize files with headers
            pd.DataFrame(columns=[
                'ticker', 'date', 'broker_code', 'broker_name', 'buy_value', 'sell_value', 
                'net_value', 'buy_lot', 'sell_lot', 'net_lot', 'avg_buy_price', 'avg_sell_price', 'broker_type'
            ]).to_csv(self.broker_csv_path, index=False)
            
            pd.DataFrame(columns=[
                'ticker', 'date', 'foreign_buy_value', 'foreign_sell_value', 'foreign_net_value',
                'foreign_buy_lot', 'foreign_sell_lot', 'foreign_net_lot'
            ]).to_csv(self.foreign_csv_path, index=False)
            
            for ticker in default_tickers:
                self._generate_mock_data_for_ticker(ticker)

    def _generate_mock_data_for_ticker(self, ticker: str):
        """Generates 30 days of realistic trading and accumulation flow for a ticker."""
        brokers = [
            {"code": "CC", "name": "Mandiri Sekuritas", "type": "local"},
            {"code": "YP", "name": "Mirae Asset Sekuritas", "type": "local"},
            {"code": "PD", "name": "Indo Premier Sekuritas", "type": "local"},
            {"code": "OD", "name": "BRI Danareksa Sekuritas", "type": "local"},
            {"code": "AK", "name": "UBS Sekuritas", "type": "foreign"},
            {"code": "ZP", "name": "Maybank Sekuritas", "type": "foreign"},
            {"code": "CS", "name": "Credit Suisse", "type": "foreign"},
            {"code": "KZ", "name": "CLSA Sekuritas", "type": "foreign"},
            {"code": "NI", "name": "BNI Sekuritas", "type": "local"},
            {"code": "DX", "name": "Bahana Sekuritas", "type": "local"}
        ]
        
        # Price range for mock values
        price_multipliers = {
            "BBCA.JK": 9000.0, "BBRI.JK": 4500.0, "BMRI.JK": 6000.0, 
            "TLKM.JK": 3000.0, "ASII.JK": 4800.0, "UNVR.JK": 2800.0, 
            "GOTO.JK": 60.0, "ADRO.JK": 2700.0, "MDKA.JK": 2400.0
        }
        base_price = price_multipliers.get(ticker, 1000.0)
        
        today = datetime.now().date()
        
        broker_rows = []
        foreign_rows = []
        
        # Generate 30 days of history
        for i in range(30):
            current_date = today - timedelta(days=i)
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
                
            # Random price variation for this date
            day_close = base_price * (1 + random.uniform(-0.04, 0.04))
            
            # --- 1. Foreign Flow Generation ---
            # Randomize foreign net buy/sell
            # 60% chance of net buy for financial blue-chips, random for others
            is_net_buy = random.random() < (0.6 if ticker in ["BBCA.JK", "BBRI.JK", "BMRI.JK"] else 0.48)
            multiplier = random.uniform(1.2, 5.0) if is_net_buy else random.uniform(0.2, 0.9)
            
            f_buy_val = random.uniform(5, 50) * 1e9 # 5B to 50B IDR
            f_sell_val = f_buy_val * multiplier
            
            # Calculate values
            f_net_val = f_buy_val - f_sell_val
            f_buy_lot = int(f_buy_val / (day_close * 100))
            f_sell_lot = int(f_sell_val / (day_close * 100))
            f_net_lot = f_buy_lot - f_sell_lot
            
            foreign_rows.append({
                'ticker': ticker,
                'date': current_date.strftime('%Y-%m-%d'),
                'foreign_buy_value': f_buy_val,
                'foreign_sell_value': f_sell_val,
                'foreign_net_value': f_net_val,
                'foreign_buy_lot': f_buy_lot,
                'foreign_sell_lot': f_sell_lot,
                'foreign_net_lot': f_net_lot
            })
            
            # --- 2. Broker Summary Generation ---
            # Total value traded for the day
            day_total_val = random.uniform(20, 150) * 1e9 # 20B to 150B IDR
            
            # Distribute traded value among brokers
            broker_shares = [random.uniform(0.1, 1.0) for _ in range(len(brokers))]
            sum_shares = sum(broker_shares)
            broker_shares = [s / sum_shares for s in broker_shares]
            
            # Decide if there is a concentration of accumulation/distribution
            # Accumulation: Foreign/Big local brokers AK, ZP, CS buy a lot, retail YP, PD, CC sell.
            # Distribution: Retail YP, PD, CC buy, big brokers sell.
            scenario = random.choice(["accum", "dist", "neutral"])
            
            for idx, b in enumerate(brokers):
                b_share_val = day_total_val * broker_shares[idx]
                
                # Set bias based on scenario
                if scenario == "accum":
                    if b['code'] in ["AK", "ZP", "CS"]:
                        buy_ratio = random.uniform(0.7, 0.95) # Big brokers buy
                    elif b['code'] in ["YP", "PD", "CC"]:
                        buy_ratio = random.uniform(0.05, 0.3) # Retail sells
                    else:
                        buy_ratio = random.uniform(0.4, 0.6)
                elif scenario == "dist":
                    if b['code'] in ["AK", "ZP", "CS"]:
                        buy_ratio = random.uniform(0.05, 0.3) # Big brokers sell
                    elif b['code'] in ["YP", "PD", "CC"]:
                        buy_ratio = random.uniform(0.7, 0.95) # Retail buys
                    else:
                        buy_ratio = random.uniform(0.4, 0.6)
                else:
                    buy_ratio = random.uniform(0.45, 0.55)
                    
                b_buy_val = b_share_val * buy_ratio
                b_sell_val = b_share_val * (1 - buy_ratio)
                b_net_val = b_buy_val - b_sell_val
                
                b_buy_lot = int(b_buy_val / (day_close * 100))
                b_sell_lot = int(b_sell_val / (day_close * 100))
                b_net_lot = b_buy_lot - b_sell_lot
                
                avg_b_price = day_close * random.uniform(0.99, 1.01)
                avg_s_price = day_close * random.uniform(0.99, 1.01)
                
                broker_rows.append({
                    'ticker': ticker,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'broker_code': b['code'],
                    'broker_name': b['name'],
                    'buy_value': b_buy_val,
                    'sell_value': b_sell_val,
                    'net_value': b_net_val,
                    'buy_lot': b_buy_lot,
                    'sell_lot': b_sell_lot,
                    'net_lot': b_net_lot,
                    'avg_buy_price': avg_b_price,
                    'avg_sell_price': avg_s_price,
                    'broker_type': b['type']
                })
                
        # Append to CSVs
        if broker_rows:
            df_broker_new = pd.DataFrame(broker_rows)
            df_broker_new.to_csv(self.broker_csv_path, mode='a', header=False, index=False)
            
        if foreign_rows:
            df_foreign_new = pd.DataFrame(foreign_rows)
            df_foreign_new.to_csv(self.foreign_csv_path, mode='a', header=False, index=False)

    def fetch_financials_and_valuation(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch fundamental financial statements and valuation data.
        Returns a dictionary containing all key quarterly/annual metrics and ratios.
        """
        import hashlib
        ticker_clean = ticker.upper().replace(".JK", "")
        h = int(hashlib.md5(ticker_clean.encode('utf-8')).hexdigest(), 16)
        
        is_bank = ticker_clean in ["BBCA", "BBRI", "BMRI", "BBNI"]
        
        # Margins & returns
        if is_bank:
            gross_margin = 70.0 + (h % 10)
            operating_margin = 40.0 + (h % 15)
            net_margin = 35.0 + (h % 15)
            roe = 15.0 + (h % 10)
            roa = 2.0 + (h % 3) * 0.5
            der = 0.1 + (h % 5) * 0.05
        else:
            gross_margin = 25.0 + (h % 40)
            operating_margin = 10.0 + (h % 25)
            net_margin = 5.0 + (h % 20)
            roe = 8.0 + (h % 22)
            roa = 3.0 + (h % 12)
            der = 0.2 + (h % 15) * 0.15
            
        # Valuation multiples
        per = 10.0 + (h % 25)
        pbv = 1.0 + (h % 50) * 0.1
        psr = 0.5 + (h % 40) * 0.1
        ev_ebitda = 6.0 + (h % 12)
        dividend_yield = (h % 8) * 1.0 if (h % 3 == 0) else 0.0
        payout_ratio = 30.0 + (h % 40) if dividend_yield > 0 else 0.0
        
        # Assets & liabilities (size in IDR)
        size_factor = 1e9 * (10 + (h % 90))
        if ticker_clean in ["BBCA", "BBRI", "BMRI"]:
            size_factor = 500 * 1e9
        elif ticker_clean in ["TLKM", "ASII"]:
            size_factor = 200 * 1e9
            
        revenue = size_factor
        gross_profit = revenue * (gross_margin / 100)
        operating_profit = revenue * (operating_margin / 100)
        net_profit = revenue * (net_margin / 100)
        
        total_equity = size_factor * 3
        total_liability = total_equity * der
        total_asset = total_equity + total_liability
        cash = total_equity * 0.15
        short_term_debt = total_liability * 0.4
        long_term_debt = total_liability * 0.6
        
        operating_cash_flow = net_profit * (0.8 + (h % 5) * 0.1)
        investing_cash_flow = -operating_cash_flow * 0.4
        financing_cash_flow = -operating_cash_flow * 0.2
        capex = operating_cash_flow * 0.3
        
        # Per share metrics
        eps = (net_profit / 1e7)
        book_value_per_share = (total_equity / 1e7)
        
        # Growth metrics
        revenue_growth = 5.0 + (h % 15)
        net_profit_growth = 4.0 + (h % 20)
        
        governance_risk = "Low" if (h % 4 != 0) else "Medium"
        if h % 10 == 0:
            governance_risk = "High"
            
        return {
            "stock_code": ticker,
            "trade_date": datetime.now().strftime("%Y-%m-%d"),
            "revenue": revenue,
            "gross_profit": gross_profit,
            "operating_profit": operating_profit,
            "net_profit": net_profit,
            "total_asset": total_asset,
            "total_liability": total_liability,
            "total_equity": total_equity,
            "cash": cash,
            "short_term_debt": short_term_debt,
            "long_term_debt": long_term_debt,
            "operating_cash_flow": operating_cash_flow,
            "investing_cash_flow": investing_cash_flow,
            "financing_cash_flow": financing_cash_flow,
            "capex": capex,
            "eps": eps,
            "book_value_per_share": book_value_per_share,
            
            # Valuation Data
            "PER": per,
            "PBV": pbv,
            "PSR": psr,
            "EV_EBITDA": ev_ebitda,
            "dividend_yield": dividend_yield,
            "payout_ratio": payout_ratio,
            "ROE": roe,
            "ROA": roa,
            "DER": der,
            "net_margin": net_margin,
            "gross_margin": gross_margin,
            "operating_margin": operating_margin,
            
            # Growth & Quality
            "revenue_growth_yoy": revenue_growth,
            "net_profit_growth_yoy": net_profit_growth,
            "governance_risk": governance_risk
        }

    def fetch_intraday_data(self, ticker: str, interval: str = "5m") -> Optional[pd.DataFrame]:
        """
        Fetch intraday bar data or fallback to simulated session metrics.
        """
        try:
            stock = yf.Ticker(ticker, session=self.session)
            df = stock.history(period="1d", interval=interval)
            if not df.empty:
                df = df.reset_index()
                df = df.rename(columns={
                    "Datetime": "datetime", "Open": "open", "High": "high", 
                    "Low": "low", "Close": "close", "Volume": "volume"
                })
                df["value"] = df["close"] * df["volume"]
                df["vwap"] = df["value"].cumsum() / df["volume"].cumsum()
                df["frequency"] = (df["volume"] / 10).astype(int) + 1
                df["interval"] = interval
                df["stock_code"] = ticker
                return df
        except Exception as e:
            print(f"Intraday yfinance warning: {e}")
            
        # Simulation fallback
        import hashlib
        ticker_clean = ticker.upper().replace(".JK", "")
        h = int(hashlib.md5(ticker_clean.encode('utf-8')).hexdigest(), 16)
        
        q = self.fetch_latest_quote(ticker)
        close_price = q.get("currentPrice", 1000.0)
        
        rows = []
        current_price = close_price * 0.98
        cum_value = 0.0
        cum_vol = 0
        
        start_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        for i in range(78):
            bar_time = start_time + timedelta(minutes=5 * i)
            change = random.uniform(-0.005, 0.006) + (0.0002 if (h % 3 == 0) else -0.0001)
            o = current_price
            c = current_price * (1 + change)
            hi = max(o, c) * (1 + random.uniform(0, 0.002))
            lo = min(o, c) * (1 - random.uniform(0, 0.002))
            vol = int(random.uniform(500, 5000) * (1.5 if (i % 10 == 0) else 1.0))
            val = c * vol
            
            cum_vol += vol
            cum_value += val
            vwap = cum_value / cum_vol if cum_vol > 0 else c
            
            rows.append({
                "stock_code": ticker,
                "datetime": bar_time.strftime("%Y-%m-%d %H:%M:%S"),
                "open": o,
                "high": hi,
                "low": lo,
                "close": c,
                "volume": vol,
                "value": val,
                "frequency": int(vol / 8) + 1,
                "vwap": vwap,
                "interval": interval
            })
            current_price = c
            
        return pd.DataFrame(rows)

    def fetch_order_book(self, ticker: str) -> Dict[str, Any]:
        """
        Generate a simulated 5-level order depth centered at the current price.
        """
        import hashlib
        ticker_clean = ticker.upper().replace(".JK", "")
        h = int(hashlib.md5(ticker_clean.encode('utf-8')).hexdigest(), 16)
        
        q = self.fetch_latest_quote(ticker)
        price = q.get("currentPrice", 1000.0)
        
        if price < 200:
            tick = 1
        elif price < 500:
            tick = 2
        elif price < 2000:
            tick = 5
        elif price < 5000:
            tick = 10
        else:
            tick = 25
            
        last_price = int(price / tick) * tick
        
        bid_prices = [last_price - tick * i for i in range(1, 6)]
        ask_prices = [last_price + tick * i for i in range(1, 6)]
        
        scenario = h % 3
        if scenario == 0:
            bid_lots = [int(random.uniform(5000, 15000) / i) for i in range(1, 6)]
            ask_lots = [int(random.uniform(2000, 8000) / i) for i in range(1, 6)]
        elif scenario == 1:
            bid_lots = [int(random.uniform(2000, 8000) / i) for i in range(1, 6)]
            ask_lots = [int(random.uniform(5000, 15000) / i) for i in range(1, 6)]
        else:
            bid_lots = [int(random.uniform(3000, 10000) / i) for i in range(1, 6)]
            ask_lots = [int(random.uniform(3000, 10000) / i) for i in range(1, 6)]
            
        total_bid = sum(bid_lots)
        total_ask = sum(ask_lots)
        bid_ask_ratio = total_bid / total_ask if total_ask > 0 else 1.0
        spread = (ask_prices[0] - bid_prices[0]) / bid_prices[0] * 100 if bid_prices[0] > 0 else 0.0
        
        result = {
            "stock_code": ticker,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "spread": spread,
            "bid_ask_ratio": bid_ask_ratio,
            "total_bid_lots": total_bid,
            "total_ask_lots": total_ask
        }
        
        for i in range(5):
            result[f"bid_price_{i+1}"] = bid_prices[i]
            result[f"bid_lot_{i+1}"] = bid_lots[i]
            result[f"ask_price_{i+1}"] = ask_prices[i]
            result[f"ask_lot_{i+1}"] = ask_lots[i]
            
        return result
