from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np

def calculate_technical_score(indicators: Dict) -> Tuple[int, List[str], List[str]]:
    """
    Calculate the technical score (0-100) based on moving averages, RSI, volume, and momentum.
    """
    score = 50
    reasons = []
    risks = []
    
    close = indicators.get("close")
    ma20 = indicators.get("ma20")
    ma50 = indicators.get("ma50")
    rsi = indicators.get("rsi")
    volume_ratio = indicators.get("volume_ratio", 1.0)
    mom_1m = indicators.get("momentum_1m", 0.0)
    mom_3m = indicators.get("momentum_3m", 0.0)
    
    if ma20 is not None:
        if close > ma20:
            score += 10
            reasons.append("Harga di atas MA20 (+10)")
        else:
            risks.append("Harga di bawah MA20 (Downtrend jk. pendek)")
            
    if ma50 is not None:
        if close > ma50:
            score += 10
            reasons.append("Harga di atas MA50 (+10)")
        else:
            risks.append("Harga di bawah MA50 (Downtrend jk. menengah)")
            
    if ma20 is not None and ma50 is not None:
        if ma20 > ma50:
            score += 10
            reasons.append("MA20 di atas MA50 / Golden Cross (+10)")
        else:
            risks.append("MA20 di bawah MA50 / Death Cross")
            
    if rsi is not None:
        if 40 <= rsi <= 70:
            score += 10
            reasons.append(f"RSI sehat di range 40-70 ({rsi:.1f}) (+10)")
        elif rsi > 75:
            score -= 15
            reasons.append(f"RSI Overbought ({rsi:.1f}) (-15)")
            risks.append(f"RSI Overbought ({rsi:.1f}) - Rawan profit taking")
        elif rsi < 30:
            risks.append(f"RSI Oversold ({rsi:.1f})")
            
    if mom_1m > 0:
        score += 10
        reasons.append("Momentum 1 bulan positif (+10)")
    else:
        risks.append("Momentum 1 bulan negatif")
        
    if mom_3m > 0:
        score += 10
        reasons.append("Momentum 3 bulan positif (+10)")
    else:
        risks.append("Momentum 3 bulan negatif")
        
    if volume_ratio > 1.0:
        score += 5
        reasons.append(f"Volume di atas rata-rata 20 hari (Ratio: {volume_ratio:.2f}x) (+5)")
    else:
        risks.append("Volume transaksi di bawah rata-rata")
        
    score = max(0, min(100, score))
    return score, reasons, risks


def calculate_flow_score(
    indicators: Dict, 
    broker_df: Optional[pd.DataFrame], 
    foreign_df: Optional[pd.DataFrame]
) -> Tuple[int, List[str], List[str], Dict[str, Any]]:
    """
    Calculate the flow score (0-100) based on Foreign Flow and Broker Summary (Bandarmologi).
    """
    score = 50
    reasons = []
    risks = []
    
    flow_data = {
        "foreign_net_1d": 0.0,
        "foreign_net_5d": 0.0,
        "foreign_net_20d": 0.0,
        "broker_net_1d": 0.0,
        "broker_net_5d": 0.0,
        "broker_net_20d": 0.0,
        "top_buyer_brokers": "N/A",
        "top_seller_brokers": "N/A",
        "broker_accumulation_signal": "Neutral",
        "broker_distribution_signal": "Neutral",
        "data_status": "Data bandarmologi tidak tersedia"
    }
    
    # Return immediately if no data is available
    if broker_df is None or broker_df.empty or foreign_df is None or foreign_df.empty:
        return score, reasons, risks, flow_data
        
    # Sort dataframes by date descending
    broker_df = broker_df.sort_values('date', ascending=False)
    foreign_df = foreign_df.sort_values('date', ascending=False)
    
    dates = foreign_df['date'].unique()
    if len(dates) == 0:
        return score, reasons, risks, flow_data
        
    flow_data["data_status"] = "Koneksi Bandarmologi Aktif"
    
    # 1. Foreign Flow Stats
    latest_date = dates[0]
    foreign_latest = foreign_df[foreign_df['date'] == latest_date]
    foreign_net_1d = float(foreign_latest['foreign_net_value'].sum()) if not foreign_latest.empty else 0.0
    
    # 5-day and 20-day foreign net flow
    unique_dates_5 = dates[:5]
    unique_dates_20 = dates[:20]
    
    foreign_5d = foreign_df[foreign_df['date'].isin(unique_dates_5)]
    foreign_net_5d = float(foreign_5d['foreign_net_value'].sum()) if not foreign_5d.empty else 0.0
    
    foreign_20d = foreign_df[foreign_df['date'].isin(unique_dates_20)]
    foreign_net_20d = float(foreign_20d['foreign_net_value'].sum()) if not foreign_20d.empty else 0.0
    
    flow_data["foreign_net_1d"] = foreign_net_1d
    flow_data["foreign_net_5d"] = foreign_net_5d
    flow_data["foreign_net_20d"] = foreign_net_20d
    
    # Points 1-3: Foreign Flow Net Buy Adjustments
    if foreign_net_1d > 0:
        score += 10
        reasons.append(f"Foreign net buy positif hari ini (Rp {foreign_net_1d:,.0f}) (+10)")
    else:
        risks.append("Foreign net sell hari ini")
        
    if foreign_net_5d > 0:
        score += 10
        reasons.append(f"Foreign net buy akumulatif 5 hari positif (Rp {foreign_net_5d:,.0f}) (+10)")
    else:
        risks.append("Foreign net sell akumulatif 5 hari")
        
    if foreign_net_20d > 0:
        score += 10
        reasons.append(f"Foreign net buy akumulatif 20 hari positif (Rp {foreign_net_20d:,.0f}) (+10)")
    else:
        risks.append("Foreign net sell akumulatif 20 hari")
        
    # Point 7: Foreign net sell 5 consecutive days
    # Check last 5 trading days
    consecutive_sell_days = 0
    for d in unique_dates_5:
        day_net = foreign_df[foreign_df['date'] == d]['foreign_net_value'].sum()
        if day_net < 0:
            consecutive_sell_days += 1
        else:
            break
            
    if consecutive_sell_days >= 5:
        score -= 15
        reasons.append("Foreign net sell 5 hari berturut-turut (-15)")
        risks.append("Aksi jual asing masif berturut-turut (Foreign Distribution)")

    # 2. Broker Summary Flow Stats
    # Get broker summaries for latest day
    broker_latest = broker_df[broker_df['date'] == latest_date].copy()
    if not broker_latest.empty:
        # Group by broker to calculate net buy value
        broker_summary = broker_latest.groupby('broker_code').agg({
            'buy_value': 'sum',
            'sell_value': 'sum',
            'net_value': 'sum'
        }).reset_index()
        
        # Sort to find Top Buyers and Top Sellers
        buyers = broker_summary[broker_summary['net_value'] > 0].sort_values('net_value', ascending=False)
        sellers = broker_summary[broker_summary['net_value'] < 0].sort_values('net_value', ascending=True)
        
        top_buyers = buyers.head(5)['broker_code'].tolist()
        top_sellers = sellers.head(5)['broker_code'].tolist()
        
        flow_data["top_buyer_brokers"] = ", ".join(top_buyers) if top_buyers else "None"
        flow_data["top_seller_brokers"] = ", ".join(top_sellers) if top_sellers else "None"
        
        # Calculate broker net flow for historical scoring
        broker_latest_net = float(broker_latest['net_value'].abs().sum() / 2) # Total buy/sell match
        flow_data["broker_net_1d"] = float(buyers.head(3)['net_value'].sum())
        
        # Points 4: Broker top net buy concentration (top 3 represent > 50% of buyers)
        total_buy_val = buyers['net_value'].sum()
        top_3_buy_val = buyers.head(3)['net_value'].sum()
        
        concentration = top_3_buy_val / total_buy_val if total_buy_val > 0 else 0.0
        
        if concentration > 0.50:
            score += 5
            reasons.append(f"Aksi beli terkonsentrasi pada 3 Broker Terbesar ({concentration*100:.1f}%) (+5)")
            flow_data["broker_accumulation_signal"] = "Accumulation"
        else:
            flow_data["broker_accumulation_signal"] = "Neutral"
            
        # Top Sellers concentration check
        total_sell_val = sellers['net_value'].abs().sum()
        top_3_sell_val = sellers.head(3)['net_value'].abs().sum()
        sell_concentration = top_3_sell_val / total_sell_val if total_sell_val > 0 else 0.0
        
        if sell_concentration > 0.50:
            flow_data["broker_distribution_signal"] = "Distribution"
            
        # Point 5 & 6: Net buy of big brokers vs price movement over last 5 days
        # Get price change over last 5 days
        close = indicators.get("close")
        ma20 = indicators.get("ma20")
        rsi = indicators.get("rsi")
        dist_high = indicators.get("distance_from_20d_high", 0.0)
        vol_ratio = indicators.get("volume_ratio", 1.0)
        
        # Calculate close 5 days ago
        hist_df = indicators.get("history")
        if hist_df is not None and len(hist_df) >= 6:
            close_5d_ago = float(hist_df.iloc[-5]['Close'])
            price_change_5d = (close / close_5d_ago - 1) * 100
        else:
            price_change_5d = 0.0
            
        # If top brokers are buying
        if top_3_buy_val > 0:
            if -3 <= price_change_5d <= 5:
                # Accumulation with quiet price (silent accumulation)
                score += 10
                reasons.append(f"Akumulasi broker besar saat harga stabil/sideways ({price_change_5d:+.1f}%) (+10)")
            elif price_change_5d < -5:
                # Net buy big but price fell sharply (retail panic selling / absorption not solid)
                score -= 10
                reasons.append("Broker besar membeli saat harga turun tajam (Indikasi absorpsi belum solid) (-10)")
                risks.append("Harga turun tajam saat broker membeli (Risiko pisau jatuh)")
                
        # Point 8: Broker top net sell is large for 3-5 days
        # Get 5-day cumulative broker net
        broker_5d = broker_df[broker_df['date'].isin(unique_dates_5)]
        if not broker_5d.empty:
            broker_5d_summary = broker_5d.groupby('broker_code').agg({'net_value': 'sum'}).reset_index()
            sellers_5d = broker_5d_summary[broker_5d_summary['net_value'] < 0].sort_values('net_value', ascending=True)
            top_3_sell_5d = sellers_5d.head(3)['net_value'].abs().sum()
            total_sell_5d = sellers_5d['net_value'].abs().sum()
            
            flow_data["broker_net_5d"] = float(top_3_sell_5d)
            
            if total_sell_5d > 0 and (top_3_sell_5d / total_sell_5d) > 0.55:
                score -= 10
                reasons.append("Distribusi broker besar terdeteksi dalam 5 hari terakhir (-10)")
                risks.append("Distribusi broker terkonsentrasi (Big Sellers active)")
                
        # Point 9: Price close to 20-day high and RSI > 75
        if dist_high < 2.0 and rsi is not None and rsi > 75:
            score -= 10
            reasons.append("Harga mendekati resistance 20 hari dan RSI Overbought (-10)")
            risks.append("Harga sudah terlalu dekat resistance 20 hari (Rawan pullback)")
            
        # Point 10: Volume rise but price does not move (candle weak / flat price)
        if vol_ratio > 1.2 and -1.0 <= price_change_5d <= 1.0:
            score -= 5
            reasons.append("Volume transaksi melonjak tetapi harga stagnan (Potensi distribusi terselubung) (-5)")
            risks.append("Churning/Distribusi: Volume tinggi tanpa kenaikan harga")
            
    score = max(0, min(100, score))
    return score, reasons, risks, flow_data


def calculate_final_score(technical_score: int, flow_score: int, has_flow_data: bool) -> Tuple[float, List[str]]:
    """
    Calculate final score based on weights: 60% Technical, 40% Flow.
    """
    warnings = []
    if not has_flow_data:
        final_score = float(technical_score)
        warnings.append("Final score hanya berdasarkan teknikal karena data flow tidak tersedia.")
    else:
        final_score = technical_score * 0.6 + flow_score * 0.4
        
    return final_score, warnings


def generate_trading_signal(
    close: float, 
    ma20: float, 
    ma50: float, 
    rsi: float, 
    mom_1m: float, 
    final_score: float, 
    flow_score: int,
    indicators: Dict,
    has_flow_data: bool,
    broker_accumulation: str
) -> Dict[str, Any]:
    """
    Generate Signal (BUY, HOLD/WATCH, AVOID) along with Entry Area, TP1, TP2, SL, and Risk-to-Reward Ratio.
    """
    signal = "HOLD / WATCH"
    reasons = []
    risks_notes = []
    
    support_20d = indicators.get("support_20d")
    resistance_20d = indicators.get("resistance_20d")
    support_50d = indicators.get("support_50d")
    resistance_50d = indicators.get("resistance_50d")
    
    # ----------------- 1. INITIAL SIGNAL EVALUATION -----------------
    is_buy_candidate = (
        final_score >= 75 and
        close > ma20 and
        close > ma50 and
        (rsi is None or rsi <= 75) and
        mom_1m > 0 and
        broker_accumulation != "Distribution"
    )
    
    is_avoid_candidate = (
        final_score < 55 or
        (close < ma20 and close < ma50) or
        mom_1m < 0 or
        (rsi is not None and rsi > 75 and indicators.get("distance_from_20d_high", 0.0) < 2.0)
    )
    
    if is_buy_candidate:
        signal = "Watchlist Prioritas"
        reasons.append("Skor kumulatif tinggi dengan tren MA20 & MA50 solid dan momentum positif.")
    elif is_avoid_candidate:
        signal = "Keluar dari Watchlist"
        reasons.append("Kondisi tren melemah (di bawah MA) atau skor kumulatif di bawah batas aman.")
    else:
        signal = "Wait and See"
        reasons.append("Saham berada dalam fase konsolidasi, sideways, atau rasio reward belum ideal.")

    # ----------------- 2. EXTENDED SETUP & DEMOTIONS -----------------
    entry_area = "No entry recommended"
    tp1 = "N/A"
    tp2 = "N/A"
    sl = "N/A"
    rr_ratio = "N/A"
    
    # Check if price is too extended from MA20 (> 8%)
    is_extended = False
    if ma20 > 0:
        pct_from_ma20 = (close - ma20) / ma20 * 100
        if pct_from_ma20 > 8.0:
            is_extended = True
            risks_notes.append("Harga sudah terlalu jauh dari MA20 (>8%)")
            
    if signal == "Watchlist Prioritas":
        if is_extended:
            signal = "Wait and See"
            reasons.clear()
            reasons.append("Sinyal diturunkan ke Wait and See karena harga sudah terlalu extended dari MA20 (>8%).")
        else:
            # Calculate Entry Area
            entry_low = round(max(ma20, close * 0.97))
            entry_high = round(close)
            
            # Stop Loss (SL)
            # SL = min(support_20d, ma50) or 4% below entry_low
            sl_candidate = min(support_20d, ma50) if (support_20d and ma50) else entry_low * 0.96
            # Ensure SL is not too far (maximum 6% below entry_low)
            sl = round(max(sl_candidate, entry_low * 0.94))
            
            # Take Profit (TP)
            tp1_candidate = resistance_20d if resistance_20d else entry_high * 1.05
            
            # Check if TP1 is too close to entry (less than 3%)
            if (tp1_candidate - entry_high) / entry_high < 0.03:
                # Use Risk-Reward based target
                risk = entry_high - sl
                tp1 = round(entry_high + 1.5 * risk) if risk > 0 else round(entry_high * 1.06)
                tp2 = round(entry_high + 2.5 * risk) if risk > 0 else round(entry_high * 1.10)
            else:
                tp1 = round(tp1_candidate)
                tp2 = round(resistance_50d) if resistance_50d else round(entry_high + 2 * (entry_high - sl))
                
            # Risk Reward Ratio Validation
            risk = entry_high - sl
            reward = tp1 - entry_high
            
            if risk <= 0 or reward <= 0:
                rr_ratio = "Invalid setup"
                signal = "Wait and See"
                reasons.clear()
                reasons.append("Sinyal diturunkan ke Wait and See karena rasio Stop Loss / Target Profit tidak valid.")
            else:
                rr = reward / risk
                rr_ratio = f"{rr:.2f}"
                
                # BUY is only valid if Risk Reward Ratio >= 1.5
                if rr < 1.5:
                    signal = "Wait and See"
                    reasons.clear()
                    reasons.append(f"Sinyal diturunkan ke Wait and See karena Risk-Reward Ratio tidak ideal ({rr:.2f} < 1.5).")
                    entry_area = f"Watch area support dekat {round(support_20d) if support_20d else 'MA20'}"
                    tp1 = round(resistance_20d) if resistance_20d else "N/A"
                    tp2 = round(resistance_50d) if resistance_50d else "N/A"
                    sl = round(min(support_20d, ma50)) if (support_20d and ma50) else "N/A"
                    rr_ratio = "N/A"
                else:
                    entry_area = f"Rp {entry_low:,} - Rp {entry_high:,}"
                    
    if signal == "Wait and See":
        # Generate passive watch setup
        entry_area = f"Watch area support dekat {round(support_20d) if support_20d else 'MA20'}"
        tp1 = round(resistance_20d) if resistance_20d else "N/A"
        tp2 = round(resistance_50d) if resistance_50d else "N/A"
        sl = round(min(support_20d, ma50)) if (support_20d and ma50) else "N/A"
        rr_ratio = "N/A"
        
    elif signal == "Keluar dari Watchlist":
        entry_area = "No entry recommended"
        tp1 = "N/A"
        tp2 = "N/A"
        sl = "N/A"
        rr_ratio = "N/A"
        
    return {
        "signal": signal,
        "entry_area": entry_area,
        "tp1": tp1,
        "tp2": tp2,
        "sl": sl,
        "risk_reward_ratio": rr_ratio,
        "entry_reason": reasons[0] if reasons else "Berdasarkan evaluasi indikator teknikal & bandarmologi.",
        "risks_notes": risks_notes
    }


def calculate_score(indicators: Dict, broker_df: Optional[pd.DataFrame] = None, foreign_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Calculate final scoring and recommendation for a stock.
    Merges technical scoring (60% weight) and flow scoring (40% weight).
    """
    # 1. Calculate Technical Score
    tech_score, tech_reasons, tech_risks = calculate_technical_score(indicators)
    
    # 2. Calculate Flow Score
    has_flow_data = broker_df is not None and not broker_df.empty and foreign_df is not None and not foreign_df.empty
    flow_score, flow_reasons, flow_risks, flow_data = calculate_flow_score(indicators, broker_df, foreign_df)
    
    # 3. Calculate Combined Final Score
    final_score, warnings = calculate_final_score(tech_score, flow_score, has_flow_data)
    
    # 4. Generate Signal and Setup
    close = indicators.get("close")
    ma20 = indicators.get("ma20")
    ma50 = indicators.get("ma50")
    rsi = indicators.get("rsi")
    mom_1m = indicators.get("momentum_1m")
    
    broker_acc = flow_data.get("broker_accumulation_signal", "Neutral")
    
    setup = generate_trading_signal(
        close=close,
        ma20=ma20,
        ma50=ma50,
        rsi=rsi,
        mom_1m=mom_1m,
        final_score=final_score,
        flow_score=flow_score,
        indicators=indicators,
        has_flow_data=has_flow_data,
        broker_accumulation=broker_acc
    )
    
    # Merge reasons and risks
    all_reasons = []
    for r in tech_reasons:
        all_reasons.append(f"[Teknikal] {r}")
    for r in flow_reasons:
        all_reasons.append(f"[Flow] {r}")
        
    all_risks = []
    for r in tech_risks:
        all_risks.append(f"[Teknikal] {r}")
    for r in flow_risks:
        all_risks.append(f"[Flow] {r}")
    for r in setup["risks_notes"]:
        all_risks.append(f"[Sinyal] {r}")
        
    # Append warnings to risks
    for w in warnings:
        all_risks.append(f"[Sistem] {w}")
        
    return {
        "technical_score": tech_score,
        "flow_score": flow_score if has_flow_data else None,
        "final_score": round(final_score, 1),
        "recommendation": setup["signal"], # Maps to BUY / HOLD / AVOID
        "reasons": all_reasons,
        "risks": all_risks if all_risks else ["Tidak ada risiko teknikal atau flow signifikan."],
        "entry_area": setup["entry_area"],
        "tp1": setup["tp1"],
        "tp2": setup["tp2"],
        "sl": setup["sl"],
        "risk_reward_ratio": setup["risk_reward_ratio"],
        "entry_reason": setup["entry_reason"],
        "flow_data": flow_data
    }
