from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np

def clean_signal_name(sig: str) -> str:
    """Helper to map legacy or mode-specific signal strings to regulatory compliant terms."""
    sig_clean = sig.strip()
    if sig_clean in ["Watchlist Prioritas", "BUY", "Strong Intraday Momentum", "Swing Breakout", "Swing Pullback", "Investment Candidate", "Scalping Prioritas", "Swing Prioritas", "Investasi Prioritas", "Accumulate Watchlist"]:
        return "Watchlist Prioritas"
    elif sig_clean in ["Wait and See", "HOLD", "WATCH", "HOLD / WATCH", "Scalping Watch", "Swing Watch", "Investment Hold", "Wait and See (Scalping)", "Wait and See (Swing)", "Wait and See (Investasi)", "Hold Watchlist"]:
        return "Wait and See"
    else:
        return "Keluar dari Watchlist"

# ================= 1. SCALPING MODE SCORING (INTRADAY / BETA MODE) =================

def calculate_scalping_score(indicators: Dict, intraday_df: pd.DataFrame, order_book: Dict) -> Dict[str, Any]:
    """
    Calculate Scalping score (0-100) and targets based on intraday VWAP, EMAs, volume spikes, and bid-ask depth.
    """
    score = 50
    reasons = []
    risks = []
    
    close = indicators.get("close", 0.0)
    
    # Intraday indicator defaults
    ema9_intra = indicators.get("ema9") or close
    ema21_intra = indicators.get("ema21") or close
    rsi = indicators.get("rsi") or 50.0
    vol_ratio = indicators.get("volume_ratio", 1.0)
    
    # 1. Intraday Momentum (25% weight)
    mom_score = 0
    if ema9_intra > ema21_intra:
        mom_score += 15
        reasons.append("EMA9 intraday berada di atas EMA21 intraday (+15)")
    else:
        risks.append("EMA9 intraday di bawah EMA21 intraday (Bearish momentum)")
        
    if 50 <= rsi <= 75:
        mom_score += 10
        reasons.append(f"RSI intraday berada di area sehat ({rsi:.1f}) (+10)")
    elif rsi > 80:
        mom_score -= 15
        reasons.append(f"RSI intraday Overbought ({rsi:.1f}) (-15)")
        risks.append("RSI intraday Overbought - rawan pembalikan instan")
    score += mom_score
    
    # 2. Volume Spike (20% weight)
    vol_score = 0
    if vol_ratio >= 2.0:
        vol_score += 20
        reasons.append(f"Lonjakan volume intraday terdeteksi ({vol_ratio:.1f}x) (+20)")
    elif vol_score >= 1.3:
        vol_score += 10
        reasons.append(f"Volume intraday di atas rata-rata ({vol_ratio:.1f}x) (+10)")
    score += vol_score
    
    # 3. Liquidity and Spread (20% weight)
    spread = order_book.get("spread", 0.1)
    spread_score = 0
    if spread <= 0.5:
        spread_score += 20
        reasons.append(f"Spread bid-ask rapat ({spread:.2f}%) (+20)")
    elif spread <= 1.0:
        spread_score += 10
        reasons.append(f"Spread bid-ask sedang ({spread:.2f}%) (+10)")
    else:
        risks.append(f"Spread bid-ask lebar ({spread:.2f}%) - risiko likuiditas tinggi")
    score += spread_score
    
    # 4. VWAP Position (15% weight)
    vwap_val = close # Default
    if not intraday_df.empty and "vwap" in intraday_df.columns:
        vwap_val = float(intraday_df.iloc[-1]["vwap"])
    vwap_score = 0
    if close > vwap_val:
        vwap_score += 15
        reasons.append("Harga bertahan di atas garis vwap intraday (+15)")
    else:
        risks.append("Harga di bawah garis vwap (Bearish trend intraday)")
    score += vwap_score
    
    # 5. Order Book Imbalance (10% weight)
    bid_ask_ratio = order_book.get("bid_ask_ratio", 1.0)
    ob_score = 0
    if bid_ask_ratio >= 1.3:
        ob_score += 10
        reasons.append(f"Imbalance Bid-Ask mendukung pembeli (Ratio: {bid_ask_ratio:.1f}x) (+10)")
    elif bid_ask_ratio >= 1.1:
        ob_score += 5
        reasons.append(f"Bid-Ask cukup seimbang cenderung beli ({bid_ask_ratio:.1f}x) (+5)")
    else:
        risks.append(f"Ask volume lebih tebal dari Bid (Ratio: {bid_ask_ratio:.1f}x)")
    score += ob_score
    
    # 6. Broker Flow & Risk penalty (10% weight combined)
    score += 5 # default flow
    if rsi > 85 or spread > 1.2:
        score -= 5
        risks.append("Penalti risiko: RSI ekstrem atau spread terlalu lebar")
        
    score = max(0, min(100, score))
    
    # Sinyal Logic
    signal = "Wait and See (Scalping)"
    if (score >= 65 and 
        close > vwap_val and 
        spread <= 1.3 and 
        rsi <= 78):
        signal = "Scalping Prioritas"
    elif (close < vwap_val or 
          spread > 1.8 or 
          rsi > 85 or 
          score < 45):
        signal = "Keluar dari Watchlist (Scalping)"
    else:
        signal = "Wait and See (Scalping)"
        
    # Scalping Risk Setup
    entry_low = round(close)
    entry_high = round(close * 1.005)
    sl = round(close * 0.985) # 1.5% SL
    tp1 = round(close * 1.015) # 1.5% TP
    tp2 = round(close * 1.03) # 3% TP
    
    risk_level = "Low"
    if spread > 0.8 or rsi > 75:
        risk_level = "High"
    elif spread > 0.4 or rsi > 65:
        risk_level = "Medium"
        
    return {
        "score": score,
        "recommendation": signal,
        "signal": signal,
        "entry_area": f"Rp {entry_low:,} - Rp {entry_high:,}" if signal != "Keluar dari Watchlist (Scalping)" else "No entry recommended",
        "sl": sl if signal != "Keluar dari Watchlist (Scalping)" else "N/A",
        "tp1": tp1 if signal != "Keluar dari Watchlist (Scalping)" else "N/A",
        "tp2": tp2 if signal != "Keluar dari Watchlist (Scalping)" else "N/A",
        "risk_level": risk_level,
        "time_horizon": "Menit s/d 1 Hari (Intraday)",
        "reasons": [f"[Scalping] {r}" for r in reasons],
        "risks": [f"[Scalping] {r}" for r in risks] if risks else ["Likuiditas dan momentum intraday terkendali."],
        "invalidation_point": "Invalidasi jika harga turun di bawah VWAP atau volume spike melambat."
    }

# ================= 2. SWING TRADING MODE SCORING =================

def calculate_swing_score(indicators: Dict, broker_df: Optional[pd.DataFrame], foreign_df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """
    Calculate Swing Trading score (0-100) based on moving averages, MACD crossovers, RSI, and broker summary.
    """
    score = 50
    reasons = []
    risks = []
    
    close = indicators.get("close", 0.0)
    ma20 = indicators.get("ma20")
    ma50 = indicators.get("ma50")
    ma200 = indicators.get("ma200") or ma50 or close
    rsi = indicators.get("rsi") or 50.0
    vol_ratio = indicators.get("volume_ratio", 1.0)
    macd = indicators.get("macd", 0.0)
    macd_sig = indicators.get("macd_signal", 0.0)
    atr = indicators.get("atr", close * 0.03)
    
    # 1. Trend Strength (25% weight)
    trend_score = 0
    if ma20 and close > ma20:
        trend_score += 10
        reasons.append("Harga di atas MA20 (+10)")
    else:
        risks.append("Harga di bawah MA20 (Tren jangka pendek melemah)")
        
    if ma50 and close > ma50:
        trend_score += 5
        reasons.append("Harga di atas MA50 (+5)")
    else:
        risks.append("Harga di bawah MA50 (Downtrend jangka menengah)")
        
    if ma20 and ma50 and ma20 > ma50:
        trend_score += 5
        reasons.append("MA20 di atas MA50 / Golden Cross (+5)")
        
    if close > ma200:
        trend_score += 5
        reasons.append("Harga di atas MA200 / Bullish jangka panjang (+5)")
    else:
        risks.append("Harga di bawah MA200 (Saham sedang downtrend panjang)")
    score += trend_score
    
    # 2. Momentum (20% weight)
    mom_score = 0
    if 45 <= rsi <= 70:
        mom_score += 10
        reasons.append(f"RSI berada di zona sehat ({rsi:.1f}) (+10)")
    elif rsi > 80:
        mom_score -= 10
        risks.append(f"RSI Overbought ({rsi:.1f}) - rawan aksi profit taking")
        
    if macd > macd_sig:
        mom_score += 10
        reasons.append("MACD Line berada di atas Signal Line (Golden Cross) (+10)")
    else:
        risks.append("MACD Line di bawah Signal Line (Bearish crossover)")
    score += mom_score
    
    # 3. Volume Confirmation (15% weight)
    vol_score = 0
    if vol_ratio >= 1.5:
        vol_score += 15
        reasons.append(f"Volume breakout terkonfirmasi ({vol_ratio:.1f}x rata-rata) (+15)")
    elif vol_ratio >= 1.0:
        vol_score += 8
        reasons.append("Volume transaksi stabil di atas rata-rata (+8)")
    else:
        risks.append("Volume transaksi di bawah rata-rata 20 hari")
    score += vol_score
    
    # 4. Broker Accumulation & Flows (20% weight combined)
    flow_score = 0
    has_flow = broker_df is not None and not broker_df.empty and foreign_df is not None and not foreign_df.empty
    
    if has_flow:
        # Check last 5 days foreign trend
        foreign_df = foreign_df.sort_values('date', ascending=False)
        dates_5 = foreign_df['date'].unique()[:5]
        foreign_5d = foreign_df[foreign_df['date'].isin(dates_5)]
        net_5d = foreign_5d['foreign_net_value'].sum() if not foreign_5d.empty else 0.0
        
        if net_5d > 0:
            flow_score += 10
            reasons.append("Asing mencatatkan Net Buy akumulatif 5 hari terakhir (+10)")
        else:
            risks.append("Asing mencatatkan Net Sell akumulatif 5 hari")
            
        # Top 3 broker concentration check on latest day
        latest_date = broker_df['date'].max()
        broker_latest = broker_df[broker_df['date'] == latest_date]
        if not broker_latest.empty:
            buyers = broker_latest[broker_latest['net_value'] > 0].sort_values('net_value', ascending=False)
            total_buy = buyers['net_value'].sum()
            top_3_buy = buyers.head(3)['net_value'].sum()
            concentration = top_3_buy / total_buy if total_buy > 0 else 0.0
            
            if concentration > 0.50:
                flow_score += 10
                reasons.append(f"Akumulasi 3 broker terbesar terkonfirmasi ({concentration*100:.1f}%) (+10)")
            else:
                flow_score += 5
    score += flow_score
    
    # 5. Sector & News Catalyst & R/R Quality (20% weight combined)
    score += 10 # Default support points
    
    score = max(0, min(100, score))
    
    # Sinyal Logic
    support_20d = indicators.get("support_20d") or close * 0.95
    resistance_20d = indicators.get("resistance_20d") or close * 1.05
    resistance_50d = indicators.get("resistance_50d") or close * 1.10
    
    # Setup calculation
    entry_low = round(max(support_20d, close * 0.96))
    entry_high = round(close)
    sl = round(entry_low - 1.5 * atr)
    tp1 = round(resistance_20d)
    tp2 = round(resistance_50d)
    
    # Validate Risk Reward Ratio
    risk = entry_high - sl
    reward = tp1 - entry_high
    rr_ratio = reward / risk if risk > 0 else 1.0
    
    signal = "Wait and See (Swing)"
    if (score >= 65 and 
        close > ma20 and 
        (38 <= rsi <= 76) and 
        rr_ratio >= 1.25):
        signal = "Swing Prioritas"
    elif (score < 45 or 
          rsi > 82 or 
          rsi < 28 or 
          (close < ma20 and close < ma50)):
        signal = "Keluar dari Watchlist (Swing)"
    else:
        signal = "Wait and See (Swing)"
        
    risk_level = "Medium"
    if rsi > 75 or close < ma50:
        risk_level = "High"
    elif close > ma50 and rsi < 55:
        risk_level = "Low"
        
    return {
        "score": score,
        "recommendation": signal,
        "signal": signal,
        "entry_area": f"Rp {entry_low:,} - Rp {entry_high:,}" if signal != "Keluar dari Watchlist (Swing)" else "No entry recommended",
        "sl": sl if signal != "Keluar dari Watchlist (Swing)" else "N/A",
        "tp1": tp1 if signal != "Keluar dari Watchlist (Swing)" else "N/A",
        "tp2": tp2 if signal != "Keluar dari Watchlist (Swing)" else "N/A",
        "risk_reward_ratio": f"{rr_ratio:.2f}" if signal != "Keluar dari Watchlist (Swing)" else "N/A",
        "risk_level": risk_level,
        "time_horizon": "2 s/d 30 Hari",
        "reasons": [f"[Swing] {r}" for r in reasons],
        "risks": [f"[Swing] {r}" for r in risks] if risks else ["Kombinasi tren dan akumulasi dalam batas aman."],
        "invalidation_point": f"Thesis invalid jika harga ditutup di bawah MA50 atau menembus stop loss Rp {sl:,}."
    }

# ================= 3. INVESTMENT MODE SCORING (FUNDAMENTAL) =================

def calculate_investment_score(financials: Dict[str, Any], close_price: float) -> Dict[str, Any]:
    """
    Calculate long-term investment score (0-100) based on earnings quality, growth, margins, DER, and valuation bands.
    """
    score = 0
    reasons = []
    risks = []
    
    # Fetch parameters
    roe = financials.get("ROE", 0.0)
    der = financials.get("DER", 1.0)
    net_margin = financials.get("net_margin", 0.0)
    gross_margin = financials.get("gross_margin", 0.0)
    rev_growth = financials.get("revenue_growth_yoy", 0.0)
    profit_growth = financials.get("net_profit_growth_yoy", 0.0)
    per = financials.get("PER", 15.0)
    pbv = financials.get("PBV", 1.5)
    eps = financials.get("eps", 0.0)
    bvps = financials.get("book_value_per_share", 0.0)
    div_yield = financials.get("dividend_yield", 0.0)
    gov_risk = financials.get("governance_risk", "Low")
    ocf = financials.get("operating_cash_flow", 0.0)
    net_profit = financials.get("net_profit", 0.0)
    
    # 1. Business Quality (20 pts max)
    qual_score = 0
    if roe >= 15.0:
        qual_score += 10
        reasons.append(f"Tingkat ROE sangat solid ({roe:.1f}%) (+10)")
    elif roe >= 10.0:
        qual_score += 5
        reasons.append(f"ROE sehat dan produktif ({roe:.1f}%) (+5)")
    else:
        risks.append(f"ROE di bawah standar industri ({roe:.1f}%)")
        
    if net_margin >= 20.0:
        qual_score += 10
        reasons.append(f"Batas Margin Bersih sangat lebar ({net_margin:.1f}%) (+10)")
    elif net_margin >= 10.0:
        qual_score += 5
        reasons.append(f"Net Profit Margin stabil ({net_margin:.1f}%) (+5)")
    score += qual_score
    
    # 2. Revenue & Earnings Growth (20 pts max)
    growth_score = 0
    if rev_growth >= 10.0:
        growth_score += 10
        reasons.append(f"Pertumbuhan pendapatan YoY kuat ({rev_growth:.1f}%) (+10)")
    elif rev_growth > 0:
        growth_score += 5
        reasons.append(f"Pendapatan tumbuh positif ({rev_growth:.1f}%) (+5)")
        
    if profit_growth >= 10.0:
        growth_score += 10
        reasons.append(f"Laba bersih tumbuh double-digit ({profit_growth:.1f}%) (+10)")
    score += growth_score
    
    # 3. Balance Sheet & Cash Flow Strength (25 pts max)
    bs_score = 0
    if der <= 0.5:
        bs_score += 10
        reasons.append(f"Rasio utang DER sangat rendah aman ({der:.2f}) (+10)")
    elif der <= 1.2:
        bs_score += 5
        reasons.append(f"DER dalam batas terkendali ({der:.2f}) (+5)")
    else:
        score -= 10
        risks.append(f"Utang DER terlalu tinggi ({der:.2f}) - Beban bunga berisiko")
        
    if ocf > 0:
        bs_score += 5
        reasons.append("Arus kas operasional positif (+5)")
    else:
        risks.append("Arus kas operasional negatif - berisiko likuiditas")
        
    if ocf > net_profit:
        bs_score += 10
        reasons.append("Kualitas laba tinggi: Arus kas operasional > Laba bersih (+10)")
    score += bs_score
    
    # 4. Valuation Multiples & Dividends (25 pts max)
    val_score = 0
    if per < 15.0:
        val_score += 10
        reasons.append(f"Valuasi PER berada di bawah rata-rata historis ({per:.1f}x) (+10)")
    elif per < 25.0:
        val_score += 5
        
    if pbv < 2.0:
        val_score += 10
        reasons.append(f"Rasio PBV wajar ({pbv:.1f}x) (+10)")
        
    if div_yield >= 4.0:
        val_score += 5
        reasons.append(f"Rasio imbal hasil dividen menarik ({div_yield:.1f}%) (+5)")
    score += val_score
    
    # 5. Governance Check (10 pts max)
    gov_score = 0
    if gov_risk == "Low":
        gov_score += 10
    elif gov_risk == "High":
        score -= 15
        risks.append("Tata kelola perusahaan (Governance) mendapat penilaian risiko tinggi")
    score += gov_score
    
    score = max(0, min(100, score))
    
    # Valuation & Status checks
    val_status = "Fair"
    if per < 11.0 or pbv < 1.1:
        val_status = "Cheap"
    elif per > 22.0 or pbv > 3.0:
        val_status = "Expensive"
        
    qual_status = "Average"
    if score >= 75:
        qual_status = "Strong"
    elif score < 50:
        qual_status = "Weak"
        
    growth_status = "Stagnant"
    if rev_growth > 8.0 and profit_growth > 8.0:
        growth_status = "Growing"
    elif rev_growth < -2.0 or profit_growth < -2.0:
        growth_status = "Declining"
        
    debt_risk = "Medium"
    if der < 0.5:
        debt_risk = "Low"
    elif der > 1.3:
        debt_risk = "High"
        
    cf_quality = "Good"
    if ocf > net_profit and ocf > 0:
        cf_quality = "Excellent"
    elif ocf < 0:
        cf_quality = "Poor"
        
    # Fair Value and Margin of Safety (Graham Formula approach or EPS multiple)
    fair_value = (eps * 13 + bvps * 1.2) / 2
    if fair_value <= 0:
        fair_value = close_price * 1.1 # Default safe
    fv_lower = fair_value * 0.85
    fv_upper = fair_value * 1.15
    mos = ((fair_value - close_price) / fair_value) * 100
    
    # Investment View Action
    inv_view = "Wait and See (Investasi)"
    if (score >= 65 and 
        qual_status in ["Strong", "Average"] and 
        val_status in ["Cheap", "Fair"] and 
        mos >= 0.0 and 
        der <= 1.8 and 
        net_profit > 0):
        inv_view = "Investasi Prioritas"
    elif (qual_status == "Weak" or 
          val_status == "Expensive" or 
          mos < -15.0 or 
          der > 2.5 or 
          net_profit < 0):
        inv_view = "Keluar dari Watchlist (Investasi)"
    else:
        inv_view = "Wait and See (Investasi)"
        
    return {
        "score": score,
        "recommendation": inv_view,
        "signal": inv_view,
        "valuation_status": val_status,
        "quality_status": qual_status,
        "growth_status": growth_status,
        "debt_risk": debt_risk,
        "cash_flow_quality": cf_quality,
        "fair_value_range": f"Rp {fv_lower:,.0f} - Rp {fv_upper:,.0f}",
        "margin_of_safety": f"{mos:+.1f}%",
        "time_horizon": "6 Bulan s/d Jangka Panjang",
        "reasons": [f"[Investasi] {r}" for r in reasons],
        "risks": [f"[Investasi] {r}" for r in risks] if risks else ["Struktur modal dan tata kelola di bawah risiko rendah."],
        "invalidation_point": "Thesis invalidasi jika pertumbuhan laba berbalik negatif 2 kuartal beruntun atau rasio DER melebihi 2.0x."
    }

# ================= LEGACY wrapper for backwards compatibility =================

def calculate_score(indicators: Dict, broker_df: Optional[pd.DataFrame] = None, foreign_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Wrapper mapping the old calculate_score calls to our advanced Swing Trading scoring model.
    Ensures that existing system processes (accuracy tracking logs, db writes) continue to run seamlessly.
    """
    swing_res = calculate_swing_score(indicators, broker_df, foreign_df)
    
    # Remap fields to match old schema expectation
    return {
        "technical_score": swing_res["score"],
        "flow_score": swing_res["score"],
        "final_score": swing_res["score"],
        "recommendation": clean_signal_name(swing_res["recommendation"]),
        "reasons": swing_res["reasons"],
        "risks": swing_res["risks"],
        "entry_area": swing_res["entry_area"],
        "tp1": swing_res["tp1"],
        "tp2": swing_res["tp2"],
        "sl": swing_res["sl"],
        "risk_reward_ratio": swing_res["risk_reward_ratio"],
        "entry_reason": swing_res["reasons"][0] if swing_res["reasons"] else "Analisis swing trading MA/RSI/Flow.",
        "flow_data": {
            "broker_accumulation_signal": "Neutral",
            "broker_distribution_signal": "Neutral"
        }
    }
