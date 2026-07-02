import pandas as pd
import numpy as np
from typing import Dict, Optional

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate the Relative Strength Index (RSI) using Wilder's smoothing technique.
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).copy()
    loss = (-delta.where(delta < 0, 0)).copy()
    
    # Calculate initial exponential moving average
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # Replace division by zero/NaN cases
    rsi = rsi.fillna(50)
    return rsi

def calculate_technical_indicators(df: pd.DataFrame) -> Optional[Dict]:
    """
    Calculate technical indicators for a given stock DataFrame.
    DataFrame must contain columns: Date, Open, High, Low, Close, Volume.
    
    Returns a dictionary of indicators at the last available trading day.
    """
    if df is None or len(df) < 60:
        # We need at least 60 rows for 3-month momentum (60 trading days) and MA50/Support50D calculations
        # If MA200 is used, we fallback gracefully when data is shorter than 200 rows.
        return None
        
    df = df.copy()
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Moving Averages
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    
    # Gracefully calculate MA200 if sufficient rows exist, else default to MA50 or close
    if len(df) >= 200:
        df['MA200'] = df['Close'].rolling(window=200).mean()
    else:
        df['MA200'] = df['MA50']
        
    # EMAs for Scalping / Intraday Trend checks
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    # RSI 14
    df['RSI'] = calculate_rsi(df['Close'], period=14)
    
    # MACD Calculation
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # ATR (Average True Range)
    df['h_l'] = df['High'] - df['Low']
    df['h_pc'] = (df['High'] - df['Close'].shift(1)).abs()
    df['l_pc'] = (df['Low'] - df['Close'].shift(1)).abs()
    df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
    df['ATR'] = df['tr'].rolling(window=14).mean()
    df['ATR'] = df['ATR'].bfill().fillna(df['Close'] * 0.02) # Fallback if nan
    
    # Volume Trend (20-day Average Volume)
    df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
    
    # Momentum (20 days ~ 1 month, 60 days ~ 3 months)
    df['Mom_1M'] = df['Close'] - df['Close'].shift(20)
    df['Mom_3M'] = df['Close'] - df['Close'].shift(60)
    
    # Percentage momentum for display
    df['Mom_1M_pct'] = (df['Close'] / df['Close'].shift(20) - 1) * 100
    df['Mom_3M_pct'] = (df['Close'] / df['Close'].shift(60) - 1) * 100
    
    # Price Boundaries (Support and Resistance)
    df['Support20D'] = df['Low'].rolling(window=20).min()
    df['Resistance20D'] = df['High'].rolling(window=20).max()
    df['Support50D'] = df['Low'].rolling(window=50).min()
    df['Resistance50D'] = df['High'].rolling(window=50).max()
    
    # High/Low for distance computations
    df['High20D'] = df['High'].rolling(window=20).max()
    df['Low20D'] = df['Low'].rolling(window=20).min()
    df['Dist_Low20D'] = (df['Close'] / df['Low20D'] - 1) * 100
    df['Dist_High20D'] = (df['High20D'] / df['Close'] - 1) * 100
    
    # Get last row (latest data)
    last_row = df.iloc[-1]
    
    # Volume ratio
    last_vol = float(last_row['Volume'])
    avg_vol_20 = float(last_row['Vol_MA20'])
    vol_ratio = last_vol / avg_vol_20 if avg_vol_20 > 0 else 1.0
    
    return {
        "date": last_row['Date'],
        "close": float(last_row['Close']),
        "open": float(last_row['Open']),
        "high": float(last_row['High']),
        "low": float(last_row['Low']),
        "volume": int(last_row['Volume']),
        "ma20": float(last_row['MA20']) if not np.isnan(last_row['MA20']) else None,
        "ma50": float(last_row['MA50']) if not np.isnan(last_row['MA50']) else None,
        "ma200": float(last_row['MA200']) if not np.isnan(last_row['MA200']) else None,
        "ema9": float(last_row['EMA9']) if not np.isnan(last_row['EMA9']) else None,
        "ema21": float(last_row['EMA21']) if not np.isnan(last_row['EMA21']) else None,
        "rsi": float(last_row['RSI']) if not np.isnan(last_row['RSI']) else None,
        "macd": float(last_row['MACD']) if not np.isnan(last_row['MACD']) else 0.0,
        "macd_signal": float(last_row['MACD_Signal']) if not np.isnan(last_row['MACD_Signal']) else 0.0,
        "macd_hist": float(last_row['MACD_Hist']) if not np.isnan(last_row['MACD_Hist']) else 0.0,
        "atr": float(last_row['ATR']),
        "vol_ma20": avg_vol_20 if not np.isnan(avg_vol_20) else None,
        "volume_ratio": vol_ratio,
        "momentum_1m": float(last_row['Mom_1M']) if not np.isnan(last_row['Mom_1M']) else 0.0,
        "momentum_3m": float(last_row['Mom_3M']) if not np.isnan(last_row['Mom_3M']) else 0.0,
        "momentum_1m_pct": float(last_row['Mom_1M_pct']) if not np.isnan(last_row['Mom_1M_pct']) else 0.0,
        "momentum_3m_pct": float(last_row['Mom_3M_pct']) if not np.isnan(last_row['Mom_3M_pct']) else 0.0,
        
        # Support and resistance
        "support_20d": float(last_row['Support20D']) if not np.isnan(last_row['Support20D']) else None,
        "resistance_20d": float(last_row['Resistance20D']) if not np.isnan(last_row['Resistance20D']) else None,
        "support_50d": float(last_row['Support50D']) if not np.isnan(last_row['Support50D']) else None,
        "resistance_50d": float(last_row['Resistance50D']) if not np.isnan(last_row['Resistance50D']) else None,
        "high_20d": float(last_row['High20D']) if not np.isnan(last_row['High20D']) else None,
        "low_20d": float(last_row['Low20D']) if not np.isnan(last_row['Low20D']) else None,
        "distance_from_20d_low": float(last_row['Dist_Low20D']) if not np.isnan(last_row['Dist_Low20D']) else 0.0,
        "distance_from_20d_high": float(last_row['Dist_High20D']) if not np.isnan(last_row['Dist_High20D']) else 0.0,
        
        # Full historical data with indicators to be used for charts
        "history": df
    }
