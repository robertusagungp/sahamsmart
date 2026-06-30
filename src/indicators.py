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
        # We need at least 60 rows for 3-month momentum (60 trading days) and MA50 calculations
        return None
        
    df = df.copy()
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Moving Averages
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    
    # RSI 14
    df['RSI'] = calculate_rsi(df['Close'], period=14)
    
    # Volume Trend (20-day Average Volume)
    df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
    
    # Momentum (20 days ~ 1 month, 60 days ~ 3 months)
    # Using shift to compare close price today with close price X days ago
    df['Mom_1M'] = df['Close'] - df['Close'].shift(20)
    df['Mom_3M'] = df['Close'] - df['Close'].shift(60)
    
    # Percentage momentum for display
    df['Mom_1M_pct'] = (df['Close'] / df['Close'].shift(20) - 1) * 100
    df['Mom_3M_pct'] = (df['Close'] / df['Close'].shift(60) - 1) * 100
    
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
        "rsi": float(last_row['RSI']) if not np.isnan(last_row['RSI']) else None,
        "vol_ma20": avg_vol_20 if not np.isnan(avg_vol_20) else None,
        "volume_ratio": vol_ratio,
        "momentum_1m": float(last_row['Mom_1M']) if not np.isnan(last_row['Mom_1M']) else 0.0,
        "momentum_3m": float(last_row['Mom_3M']) if not np.isnan(last_row['Mom_3M']) else 0.0,
        "momentum_1m_pct": float(last_row['Mom_1M_pct']) if not np.isnan(last_row['Mom_1M_pct']) else 0.0,
        "momentum_3m_pct": float(last_row['Mom_3M_pct']) if not np.isnan(last_row['Mom_3M_pct']) else 0.0,
        # Full historical data with indicators to be used for charts
        "history": df
    }
