from typing import Dict, List, Tuple

def calculate_score(indicators: Dict) -> Dict:
    """
    Calculate scoring and recommendation for a stock based on its indicators.
    Scoring logic:
    - Base score: 50
    - Close > MA20: +10
    - Close > MA50: +10
    - MA20 > MA50: +10
    - RSI between 40 and 70 (inclusive): +10
    - RSI > 75: -15
    - Momentum 1M > 0: +10
    - Momentum 3M > 0: +10
    - Volume last day > MA20 Volume: +5
    - Minimum score: 0, Maximum score: 100
    
    Recommendations:
    - Score >= 75: BUY
    - Score >= 50 and < 75: WATCH
    - Score < 50: AVOID
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
    
    # 1. Close vs MA20
    if ma20 is not None:
        if close > ma20:
            score += 10
            reasons.append("Harga di atas MA20 (+10)")
        else:
            risks.append("Harga berada di bawah MA20 (Downtrend jangka pendek)")
            
    # 2. Close vs MA50
    if ma50 is not None:
        if close > ma50:
            score += 10
            reasons.append("Harga di atas MA50 (+10)")
        else:
            risks.append("Harga berada di bawah MA50 (Downtrend jangka menengah)")
            
    # 3. MA20 vs MA50
    if ma20 is not None and ma50 is not None:
        if ma20 > ma50:
            score += 10
            reasons.append("MA20 di atas MA50 / Golden Cross (+10)")
        else:
            risks.append("MA20 di bawah MA50 / Death Cross (Downtrend terkonfirmasi)")
            
    # 4. RSI
    if rsi is not None:
        if 40 <= rsi <= 70:
            score += 10
            reasons.append(f"RSI berada di zona netral/sehat ({rsi:.1f}) (+10)")
        elif rsi > 75:
            score -= 15
            reasons.append(f"RSI menunjukkan overbought ({rsi:.1f}) (-15)")
            risks.append(f"RSI Overbought ({rsi:.1f}) - Rawan aksi profit taking")
        elif rsi < 30:
            risks.append(f"RSI Oversold ({rsi:.1f}) - Penjualan jenuh, potensi rebound mendesak")
            
    # 5. Momentum 1M
    if mom_1m > 0:
        score += 10
        reasons.append("Momentum harga 1 bulan positif (+10)")
    else:
        risks.append("Momentum 1 bulan negatif (Tren jangka pendek melemah)")
        
    # 6. Momentum 3M
    if mom_3m > 0:
        score += 10
        reasons.append("Momentum harga 3 bulan positif (+10)")
    else:
        risks.append("Momentum 3 bulan negatif (Tren jangka menengah melemah)")
        
    # 7. Volume vs 20-day average
    if volume_ratio > 1.0:
        score += 5
        reasons.append(f"Volume transaksi di atas rata-rata 20 hari (Ratio: {volume_ratio:.2f}x) (+5)")
    else:
        risks.append("Volume transaksi di bawah rata-rata (Partisipasi pasar lemah)")
        
    # Clamp score
    score = max(0, min(100, score))
    
    # Recommendation
    if score >= 75:
        recommendation = "BUY"
    elif score >= 50:
        recommendation = "WATCH"
    else:
        recommendation = "AVOID"
        
    return {
        "score": score,
        "recommendation": recommendation,
        "reasons": reasons,
        "risks": risks if risks else ["Tidak ada risiko teknikal signifikan yang terdeteksi."]
    }
