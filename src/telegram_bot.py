import requests
import io
from typing import Dict, Tuple, Any

def send_telegram_alert(bot_token: str, chat_id: str, record: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Sends a beautifully HTML-formatted stock alert to a Telegram Group/Channel via Bot API.
    """
    if not bot_token or not chat_id:
        return False, "Token Bot atau Chat ID tidak lengkap. Konfigurasikan di sidebar."
        
    ticker = record.get("ticker", "N/A").split(".")[0] # Clean ticker (e.g., BBCA instead of BBCA.JK)
    name = record.get("name", "N/A")
    signal = record.get("recommendation", "N/A")
    tech_score = record.get("technical_score", "N/A")
    flow_score = record.get("flow_score", "N/A")
    final_score = record.get("score", "N/A")
    entry_area = record.get("entry_area", "N/A")
    
    # Extract TP1, TP2, and SL values
    tp1 = record.get("tp1", "N/A")
    tp2 = record.get("tp2", "N/A")
    sl = record.get("sl", "N/A")
    
    tp1_str = f"Rp {tp1:,}" if isinstance(tp1, (int, float)) else str(tp1)
    tp2_str = f"Rp {tp2:,}" if isinstance(tp2, (int, float)) else str(tp2)
    sl_str = f"Rp {sl:,}" if isinstance(sl, (int, float)) else str(sl)
    
    rr = record.get("risk_reward_ratio", "N/A")
    reason = record.get("entry_reason", "N/A")
    
    # Clean and compile risks notes
    risks = record.get("risks", [])
    clean_risks = [r.replace("[Teknikal] ", "").replace("[Flow] ", "").replace("[Sinyal] ", "") for r in risks if "Tidak ada" not in r]
    risk_note = "; ".join(clean_risks[:3]) if clean_risks else "Tidak ada risiko signifikan."
    
    # Set signal icon with regulatory compliant terms
    if signal in ["Watchlist Prioritas", "BUY"]:
        signal_emoji = "🟢 Watchlist Prioritas"
    elif signal in ["Wait and See", "HOLD", "WATCH", "HOLD / WATCH"]:
        signal_emoji = "🟡 Wait and See"
    else:
        signal_emoji = "🔴 Keluar dari Watchlist"
    
    # Build HTML Message
    message = f"""👑 <b>SMART SAHAM PREMIUM ALERT</b> 👑

📊 Ticker: <b>{ticker} - {name}</b>
Sinyal: <b>{signal_emoji}</b>

🔢 <b>Skor Analisis:</b>
• Skor Teknis (60%): <b>{tech_score}</b>
• Skor Flow (40%): <b>{flow_score}</b>
• Skor Akhir: <b>{final_score}</b>

🎯 <b>Setup Trading:</b>
• Area Entri: <code>{entry_area}</code>
• Target Profit 1 (TP1): <code>{tp1_str}</code>
• Target Profit 2 (TP2): <code>{tp2_str}</code>
• Batas Stop Loss (SL): <code>{sl_str}</code>
• R/R Ratio: <b>{rr}</b>

💡 <b>Alasan Utama:</b>
<i>{reason}</i>

⚠️ <b>Catatan Risiko:</b>
<i>{risk_note}</i>

⚠️ <b>Disclaimer & Informasi:</b>
<i>Aplikasi ini bukan rekomendasi saham untuk beli/jual, melainkan AI stock screening & risk monitoring platform. Segala keputusan transaksi ada pada tangan pengguna sendiri.</i>

<i>Dikirim otomatis via Dashboard Smart Saham Premium</i>"""

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        res_json = response.json()
        if response.status_code == 200 and res_json.get("ok"):
            return True, "Alert berhasil dikirim ke Telegram!"
        else:
            err_desc = res_json.get("description", "Unknown error")
            return False, f"Telegram API Error: {err_desc}"
    except Exception as e:
        return False, f"Koneksi gagal: {str(e)}"

def send_telegram_photo(bot_token: str, chat_id: str, img_bytes: io.BytesIO, caption: str) -> Tuple[bool, str]:
    """
    Sends a photo (image bytes) to a Telegram Group/Channel using the sendPhoto endpoint.
    """
    if not bot_token or not chat_id:
        return False, "Token Bot atau Chat ID tidak lengkap. Konfigurasikan di sidebar."
        
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    
    # Ensure image bytes is at beginning
    img_bytes.seek(0)
    
    files = {
        "photo": ("share_card.png", img_bytes, "image/png")
    }
    payload = {
        "chat_id": chat_id,
        "caption": caption,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=payload, files=files, timeout=15)
        res_json = response.json()
        if response.status_code == 200 and res_json.get("ok"):
            return True, "Share Card berhasil dikirim ke Telegram!"
        else:
            err_desc = res_json.get("description", "Unknown error")
            return False, f"Telegram API Error: {err_desc}"
    except Exception as e:
        return False, f"Koneksi gagal: {str(e)}"
