import pandas as pd
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from src.data_loader import StockDataLoader
from src.storage import AnalysisStorage

def run_portfolio_evaluation(storage: AnalysisStorage, loader: StockDataLoader, username: str):
    """
    Cycles through all user trades (both open and closed) and evaluates:
    1. Current Price (for open positions)
    2. Unrealized P/L and ROI
    3. Realized P/L and ROI (for closed positions)
    4. TP1, TP2, and SL Hits & Dates
    5. Max Gain & Max Drawdown after buy date
    6. Accuracy comparison against the app's signal snapshot at buy.
    """
    df_trades = storage.get_real_trades(username)
    if df_trades.empty:
        return
        
    today = date.today()
    
    for _, trade in df_trades.iterrows():
        trade_id = int(trade["trade_id"])
        ticker = trade["ticker"]
        buy_price = float(trade["buy_price"])
        lot_quantity = int(trade["lot_quantity"])
        status = trade["status"]
        app_signal = trade["app_signal_at_buy"]
        
        # Convert buy_date to date object
        buy_date_raw = trade["buy_date"]
        if isinstance(buy_date_raw, str):
            buy_date = datetime.strptime(buy_date_raw, "%Y-%m-%d").date()
        elif isinstance(buy_date_raw, datetime):
            buy_date = buy_date_raw.date()
        else:
            buy_date = buy_date_raw
            
        tp1 = float(trade["tp1_at_buy"]) if trade["tp1_at_buy"] else None
        tp2 = float(trade["tp2_at_buy"]) if trade["tp2_at_buy"] else None
        sl = float(trade["sl_at_buy"]) if trade["sl_at_buy"] else None
        
        # Fetch historical data to evaluate TP/SL hits and max moves
        # Pull 2 years to cover older dates
        df_hist = loader.fetch_historical_data(ticker, period="2y")
        
        eval_record = {
            "trade_id": trade_id,
            "ticker": ticker,
            "current_price": buy_price,
            "realized_profit_loss": 0.0,
            "unrealized_profit_loss": 0.0,
            "return_percentage": 0.0,
            "holding_days": 0,
            "tp1_hit": False,
            "tp1_hit_date": None,
            "tp2_hit": False,
            "tp2_hit_date": None,
            "sl_hit": False,
            "sl_hit_date": None,
            "max_gain_after_buy": 0.0,
            "max_drawdown_after_buy": 0.0,
            "prediction_result": "Still Running",
            "prediction_result_detail": "Posisi baru dibuka, sedang dipantau."
        }
        
        # 1. Price Evaluation (if history is available)
        if df_hist is not None and not df_hist.empty:
            df_hist['Date_Only'] = pd.to_datetime(df_hist['Date']).dt.date
            
            # Filter history starting from buy_date
            df_after_buy = df_hist[df_hist['Date_Only'] >= buy_date].sort_values('Date_Only').copy()
            
            if not df_after_buy.empty:
                # Latest close price
                current_price = float(df_after_buy.iloc[-1]['Close'])
                eval_record["current_price"] = current_price
                
                # Check target profit and stop loss hits
                tp1_hit = False
                tp1_date = None
                tp2_hit = False
                tp2_date = None
                sl_hit = False
                sl_date = None
                
                max_high = buy_price
                min_low = buy_price
                
                for _, day in df_after_buy.iterrows():
                    day_high = float(day['High'])
                    day_low = float(day['Low'])
                    day_date = day['Date_Only']
                    
                    if day_high > max_high:
                        max_high = day_high
                    if day_low < min_low:
                        min_low = day_low
                        
                    # Check TP1
                    if tp1 and not tp1_hit and day_high >= tp1:
                        tp1_hit = True
                        tp1_date = day_date
                    # Check TP2
                    if tp2 and not tp2_hit and day_high >= tp2:
                        tp2_hit = True
                        tp2_date = day_date
                    # Check SL
                    if sl and not sl_hit and day_low <= sl:
                        sl_hit = True
                        sl_date = day_date
                        
                eval_record["tp1_hit"] = tp1_hit
                eval_record["tp1_hit_date"] = tp1_date
                eval_record["tp2_hit"] = tp2_hit
                eval_record["tp2_hit_date"] = tp2_date
                eval_record["sl_hit"] = sl_hit
                eval_record["sl_hit_date"] = sl_date
                
                # Calculate max percentage moves
                eval_record["max_gain_after_buy"] = (max_high - buy_price) / buy_price * 100
                eval_record["max_drawdown_after_buy"] = (min_low - buy_price) / buy_price * 100
                
        # 2. Holding Days
        if status == "Closed Position":
            sell_date_raw = trade["sell_date"]
            if isinstance(sell_date_raw, str):
                sell_date = datetime.strptime(sell_date_raw, "%Y-%m-%d").date()
            elif isinstance(sell_date_raw, datetime):
                sell_date = sell_date_raw.date()
            else:
                sell_date = sell_date_raw
            eval_record["holding_days"] = max(0, (sell_date - buy_date).days)
        else:
            eval_record["holding_days"] = max(0, (today - buy_date).days)
            
        # 3. ROI and P/L calculations
        if status == "Closed Position":
            sell_price = float(trade["sell_price"])
            eval_record["return_percentage"] = (sell_price - buy_price) / buy_price * 100
            eval_record["realized_profit_loss"] = (sell_price - buy_price) * lot_quantity * 100
            eval_record["unrealized_profit_loss"] = 0.0
        else:
            current_price = eval_record["current_price"]
            eval_record["return_percentage"] = (current_price - buy_price) / buy_price * 100
            eval_record["unrealized_profit_loss"] = (current_price - buy_price) * lot_quantity * 100
            eval_record["realized_profit_loss"] = 0.0
            
        # 4. Accuracy Assessment against signal prediction
        ret = eval_record["return_percentage"]
        tp1_hit = eval_record["tp1_hit"]
        tp2_hit = eval_record["tp2_hit"]
        sl_hit = eval_record["sl_hit"]
        
        if status == "Open Position" and eval_record["holding_days"] < 1:
            eval_record["prediction_result"] = "Still Running"
            eval_record["prediction_result_detail"] = "Sinyal masih berjalan (posisi baru)."
        else:
            if app_signal == "BUY":
                if ret > 0:
                    eval_record["prediction_result"] = "Correct"
                    detail = f"Harga naik setelah sinyal BUY (+{ret:.1f}%)."
                    if tp1_hit:
                        detail += " Target TP1 Tercapai."
                    if tp2_hit:
                        detail += " Target TP2 Tercapai."
                    eval_record["prediction_result_detail"] = detail
                else:
                    eval_record["prediction_result"] = "Wrong"
                    detail = f"Harga turun setelah sinyal BUY ({ret:.1f}%)."
                    if sl_hit:
                        detail += " Sinyal menyentuh Stop Loss."
                    eval_record["prediction_result_detail"] = detail
                    
            elif app_signal in ["HOLD / WATCH", "HOLD", "WATCH"]:
                if ret > -3.0:
                    eval_record["prediction_result"] = "Correct"
                    eval_record["prediction_result_detail"] = f"Sideways atau naik sesuai sinyal HOLD ({ret:+.1f}%)."
                else:
                    eval_record["prediction_result"] = "Wrong"
                    eval_record["prediction_result_detail"] = f"Tren rusak/harga turun melewati batas toleransi HOLD ({ret:.1f}%)."
                    
            elif app_signal == "AVOID":
                if ret < 0:
                    eval_record["prediction_result"] = "Correct"
                    eval_record["prediction_result_detail"] = f"Harga turun sesuai prediksi sinyal AVOID ({ret:.1f}%)."
                else:
                    eval_record["prediction_result"] = "Wrong"
                    eval_record["prediction_result_detail"] = f"Harga malah naik setelah sinyal AVOID (+{ret:.1f}%)."
            else:
                eval_record["prediction_result"] = "Neutral"
                eval_record["prediction_result_detail"] = f"Posisi selesai dengan return {ret:+.1f}%."
                
        # 5. Persist to database
        storage.save_or_update_evaluation(eval_record)
