import os
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

def generate_share_card(trade_data: dict, template: str = "Formal Dark", size_ratio: str = "1080x1080") -> io.BytesIO:
    """
    Generates a professional closed-trade share card with multiple templates and aspect ratios.
    Aspect ratios:
    - "1080x1080" (Square Feed)
    - "1080x1920" (Story)
    - "1200x628" (Telegram Preview)
    """
    # 1. Determine Dimensions
    if size_ratio == "1080x1920":
        width, height = 1080, 1920
    elif size_ratio == "1200x628":
        width, height = 1200, 628
    else:
        width, height = 1080, 1080
        
    # 2. Define Theme Palette
    is_light = template == "Formal Light"
    is_exec = template == "Executive Summary"
    
    if is_light:
        bg_canvas = "#f8fafc"
        bg_card = "#ffffff"
        border_color = "#cbd5e1"
        text_primary = "#0f172a"
        text_secondary = "#475569"
        text_muted = "#94a3b8"
        divider_color = "#e2e8f0"
    elif is_exec:
        bg_canvas = "#050505"
        bg_card = "#111111"
        border_color = "#262626"
        text_primary = "#ffffff"
        text_secondary = "#a3a3a3"
        text_muted = "#525252"
        divider_color = "#1f1f1f"
    else: # Formal Dark
        bg_canvas = "#0b0c10"
        bg_card = "#121214"
        border_color = "#1f2937"
        text_primary = "#ffffff"
        text_secondary = "#94a3b8"
        text_muted = "#4b5563"
        divider_color = "#1f2937"

    # Fetch values
    ticker = str(trade_data.get("ticker", "UNKNOWN")).split(".")[0]
    buy_price = float(trade_data.get("buy_price", 0))
    sell_price = float(trade_data.get("sell_price", 0))
    roi = float(trade_data.get("return_percentage", 0))
    realized_pl = float(trade_data.get("realized_profit_loss", 0))
    holding_days = int(trade_data.get("holding_days", 0))
    exit_type = str(trade_data.get("exit_type", "Manual Sell"))
    app_signal = str(trade_data.get("app_signal_at_buy", "BUY"))
    
    buy_date = str(trade_data.get("buy_date", "N/A"))
    sell_date = str(trade_data.get("sell_date", "N/A"))
    entry_area = str(trade_data.get("entry_area_at_buy", f"Rp {buy_price:,.0f}"))
    tp1 = trade_data.get("tp1_at_buy")
    tp2 = trade_data.get("tp2_at_buy")
    sl = trade_data.get("sl_at_buy")
    
    tp1_hit = "Yes" if trade_data.get("tp1_hit") else "No"
    tp2_hit = "Yes" if trade_data.get("tp2_hit") else "No"
    sl_hit = "Yes" if trade_data.get("sl_hit") else "No"
    
    max_gain = float(trade_data.get("max_gain_after_buy", 0))
    max_dd = float(trade_data.get("max_drawdown_after_buy", 0))
    
    tech_score = int(trade_data.get("technical_score_at_buy", 0))
    flow_score = int(trade_data.get("flow_score_at_buy", 0))
    final_score = float(trade_data.get("final_score_at_buy", 0))
    reason = str(trade_data.get("reason_at_buy", "N/A"))
    
    # Outcomes status
    if roi > 0.05:
        status_label = "PROFIT"
        accent_color = "#10b981" # green
        accent_bg = "#064e3b"
    elif roi < -0.05:
        status_label = "LOSS"
        accent_color = "#ef4444" # red
        accent_bg = "#7f1d1d"
    else:
        status_label = "BREAKEVEN"
        accent_color = "#f59e0b" # orange/yellow
        accent_bg = "#78350f"

    # Font sizing mappings based on canvas width
    font_paths = [
        "C:\\Windows\\Fonts\\segoeuib.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    
    def get_font(size, bold=False):
        for path in font_paths:
            if os.path.exists(path):
                try:
                    if bold and "segoeuib" in path.lower():
                        return ImageFont.truetype(path, size)
                    return ImageFont.truetype(path, size)
                except:
                    pass
        return ImageFont.load_default()

    font_title = get_font(28, bold=True)
    font_ticker = get_font(84, bold=True)
    font_roi = get_font(64, bold=True)
    font_label = get_font(18, bold=False)
    font_value = get_font(24, bold=True)
    font_value_sm = get_font(20, bold=True)
    font_footer = get_font(16, bold=False)
    
    # 3. Initialize Pillow image
    img = Image.new("RGBA", (width, height), bg_canvas)
    draw = ImageDraw.Draw(img)
    
    # Draw central rounded container card
    margin_x, margin_y = 40, 40
    draw.rounded_rectangle(
        [margin_x, margin_y, width - margin_x, height - margin_y],
        radius=30, fill=bg_card, outline=border_color, width=3
    )
    
    # Draw Header Elements
    draw.text((80, 80), "👑 SMART STOCK SIGNAL", fill="#f59e0b", font=font_title)
    draw.text((80, 115), f"TRADE CLOSED / EXIT RESULT  •  {sell_date}", fill=text_secondary, font=font_label)
    draw.line([80, 150, width - 80, 150], fill=divider_color, width=2)
    
    # 4. RATIO-BASED LAYOUT DRAWERS
    if size_ratio == "1200x628": # TELEGRAM PREVIEW
        # Large Ticker & ROI side-by-side
        draw.text((80, 180), ticker, fill=text_primary, font=font_ticker)
        
        # Outcome label and ROI badge
        draw.rounded_rectangle([380, 180, 520, 215], radius=6, fill=accent_bg)
        draw.text((395, 188), status_label, fill=accent_color, font=get_font(14, bold=True))
        
        roi_text = f"{roi:+.2f}%"
        draw.rounded_rectangle([550, 175, 850, 270], radius=12, fill=accent_color)
        draw.text((580, 190), roi_text, fill="#ffffff", font=font_roi)
        
        # Signal tag
        draw.rounded_rectangle([80, 280, 260, 315], radius=6, fill=divider_color)
        draw.text((95, 288), f"Signal at Buy: {app_signal}", fill=text_secondary, font=get_font(14, bold=True))
        
        # Grid of details (4 columns x 2 rows)
        col_w = 260
        row1_y = 350
        row2_y = 450
        
        # Col 0
        draw.text((80, row1_y), "BUY PRICE", fill=text_secondary, font=font_label)
        draw.text((80, row1_y + 30), f"Rp {buy_price:,.0f}", fill=text_primary, font=font_value)
        
        draw.text((80, row2_y), "SELL PRICE", fill=text_secondary, font=font_label)
        draw.text((80, row2_y + 30), f"Rp {sell_price:,.0f}", fill=text_primary, font=font_value)
        
        # Col 1
        draw.text((80 + col_w, row1_y), "HOLDING TIME", fill=text_secondary, font=font_label)
        draw.text((80 + col_w, row1_y + 30), f"{holding_days} Days", fill=text_primary, font=font_value)
        
        draw.text((80 + col_w, row2_y), "REALIZED P/L", fill=text_secondary, font=font_label)
        draw.text((80 + col_w, row2_y + 30), f"Rp {realized_pl:+,.0f}", fill=accent_color, font=font_value)
        
        # Col 2
        draw.text((80 + 2*col_w, row1_y), "TP1 / TP2 HIT", fill=text_secondary, font=font_label)
        draw.text((80 + 2*col_w, row1_y + 30), f"{tp1_hit} / {tp2_hit}", fill=text_primary, font=font_value)
        
        draw.text((80 + 2*col_w, row2_y), "SL HIT", fill=text_secondary, font=font_label)
        draw.text((80 + 2*col_w, row2_y + 30), sl_hit, fill=text_primary, font=font_value)
        
        # Col 3
        draw.text((80 + 3*col_w, row1_y), "MAX GAIN / DD", fill=text_secondary, font=font_label)
        draw.text((80 + 3*col_w, row1_y + 30), f"{max_gain:+.1f}% / {max_dd:+.1f}%", fill=text_primary, font=font_value_sm)
        
        draw.text((80 + 3*col_w, row2_y), "FINAL SCORE", fill=text_secondary, font=font_label)
        draw.text((80 + 3*col_w, row2_y + 30), f"{final_score} (T:{tech_score}/F:{flow_score})", fill=text_primary, font=font_value_sm)
        
        # Footer
        draw.line([80, 540, width - 80, 540], fill=divider_color, width=1)
        draw.text((80, 560), "For tracking & evaluation only. Not financial advice.", fill=text_muted, font=font_footer)
        draw.text((width - 320, 560), f"Generated: {datetime.now().strftime('%Y-%m-%d')}", fill=text_muted, font=font_footer)

    elif size_ratio == "1080x1920": # INSTAGRAM STORY (Long vertical)
        # Big center layout
        draw.text((80, 220), ticker, fill=text_primary, font=font_ticker)
        
        # ROI badge centered and large
        draw.rounded_rectangle([80, 340, width - 80, 480], radius=20, fill=accent_color)
        roi_text = f"{roi:+.2f}%"
        draw.text((120, 370), roi_text, fill="#ffffff", font=get_font(72, bold=True))
        
        # Outcome & signal details tag
        draw.rounded_rectangle([80, 520, 260, 560], radius=8, fill=accent_bg)
        draw.text((95, 530), f"RESULT: {status_label}", fill=accent_color, font=get_font(16, bold=True))
        
        draw.rounded_rectangle([290, 520, 520, 560], radius=8, fill=divider_color)
        draw.text((305, 530), f"SIGNAL: {app_signal} (Sc: {final_score})", fill=text_secondary, font=get_font(16, bold=True))
        
        draw.line([80, 600, width - 80, 600], fill=divider_color, width=2)
        
        # Visual Grid layout (2 columns)
        col_w = 460
        row_y = 640
        step_y = 130
        
        # Row 1
        draw.text((80, row_y), "BUY PRICE", fill=text_secondary, font=font_label)
        draw.text((80, row_y + 30), f"Rp {buy_price:,.0f} ({buy_date})", fill=text_primary, font=font_value)
        
        draw.text((80 + col_w, row_y), "SELL PRICE", fill=text_secondary, font=font_label)
        draw.text((80 + col_w, row_y + 30), f"Rp {sell_price:,.0f} ({sell_date})", fill=text_primary, font=font_value)
        
        # Row 2
        draw.text((80, row_y + step_y), "NET REALIZED P/L", fill=text_secondary, font=font_label)
        draw.text((80, row_y + step_y + 30), f"Rp {realized_pl:+,.0f}", fill=accent_color, font=font_value)
        
        draw.text((80 + col_w, row_y + step_y), "HOLDING PERIOD", fill=text_secondary, font=font_label)
        draw.text((80 + col_w, row_y + step_y + 30), f"{holding_days} Days", fill=text_primary, font=font_value)
        
        # Row 3
        draw.text((80, row_y + 2*step_y), "TP1 / TP2 TARGET", fill=text_secondary, font=font_label)
        draw.text((80, row_y + 2*step_y + 30), f"Rp {tp1:,.0f} / Rp {tp2:,.0f}" if (tp1 and tp2) else "N/A", fill=text_primary, font=font_value_sm)
        
        draw.text((80 + col_w, row_y + 2*step_y), "STOP LOSS LIMIT", fill=text_secondary, font=font_label)
        draw.text((80 + col_w, row_y + 2*step_y + 30), f"Rp {sl:,.0f}" if sl else "N/A", fill=text_primary, font=font_value)
        
        # Row 4
        draw.text((80, row_y + 3*step_y), "TP1 / TP2 HITS", fill=text_secondary, font=font_label)
        draw.text((80, row_y + 3*step_y + 30), f"{tp1_hit} / {tp2_hit}", fill=text_primary, font=font_value)
        
        draw.text((80 + col_w, row_y + 3*step_y), "STOP LOSS HIT", fill=text_secondary, font=font_label)
        draw.text((80 + col_w, row_y + 3*step_y + 30), sl_hit, fill=text_primary, font=font_value)
        
        # Row 5
        draw.text((80, row_y + 4*step_y), "MAX GAIN AFTER BUY", fill=text_secondary, font=font_label)
        draw.text((80, row_y + 4*step_y + 30), f"{max_gain:+.2f}%", fill="#10b981", font=font_value)
        
        draw.text((80 + col_w, row_y + 4*step_y), "MAX DRAWDOWN AFTER BUY", fill=text_secondary, font=font_label)
        draw.text((80 + col_w, row_y + 4*step_y + 30), f"{max_dd:+.2f}%", fill="#ef4444", font=font_value)
        
        # Row 6: Score details & Reason
        draw.line([80, row_y + 5*step_y, width - 80, row_y + 5*step_y], fill=divider_color, width=1)
        
        draw.text((80, row_y + 5*step_y + 30), "TECHNICAL SCORE", fill=text_secondary, font=font_label)
        draw.text((80, row_y + 5*step_y + 60), f"{tech_score}/100", fill=text_primary, font=font_value)
        
        draw.text((80 + col_w, row_y + 5*step_y + 30), "FLOW SCORE", fill=text_secondary, font=font_label)
        draw.text((80 + col_w, row_y + 5*step_y + 60), f"{flow_score}/100", fill=text_primary, font=font_value)
        
        # Entry Reason text wrapper
        draw.text((80, row_y + 6.3*step_y), "MAIN ENTRY REASON", fill=text_secondary, font=font_label)
        wrapped_reason = reason[:85] + "..." if len(reason) > 85 else reason
        draw.text((80, row_y + 6.3*step_y + 30), wrapped_reason, fill=text_primary, font=get_font(18, bold=False))
        
        # Footer
        draw.line([80, height - 160, width - 80, height - 160], fill=divider_color, width=2)
        draw.text((80, height - 130), "For tracking & evaluation only. Not financial advice.", fill=text_muted, font=font_footer)
        draw.text((width - 320, height - 130), f"Generated: {datetime.now().strftime('%Y-%m-%d')}", fill=text_muted, font=font_footer)

    else: # 1080x1080 INSTAGRAM SQUARE FEED (Standard)
        # Left side: Ticker and signal details
        draw.text((80, 180), ticker, fill=text_primary, font=font_ticker)
        
        # Signal tag & outcome badges
        draw.rounded_rectangle([80, 290, 240, 325], radius=6, fill=accent_bg)
        draw.text((95, 298), status_label, fill=accent_color, font=get_font(14, bold=True))
        
        draw.rounded_rectangle([270, 290, 480, 325], radius=6, fill=divider_color)
        draw.text((285, 298), f"Signal: {app_signal} (Sc: {final_score})", fill=text_secondary, font=get_font(14, bold=True))
        
        # Right side: Large ROI badge
        draw.rounded_rectangle([530, 180, 1000, 320], radius=20, fill=accent_color)
        roi_text = f"{roi:+.2f}%"
        draw.text((580, 210), roi_text, fill="#ffffff", font=font_roi)
        draw.text((580, 280), "REALIZED RETURN", fill="#f1f5f9", font=font_label)
        
        draw.line([80, 360, width - 80, 360], fill=divider_color, width=2)
        
        if is_exec:
            # Minimal Exec summary grid layout
            col_w = 460
            row_y = 420
            step_y = 150
            
            draw.text((80, row_y), "BUY PRICE", fill=text_secondary, font=font_label)
            draw.text((80, row_y + 30), f"Rp {buy_price:,.0f}", fill=text_primary, font=font_value)
            draw.text((80 + col_w, row_y), "SELL PRICE", fill=text_secondary, font=font_label)
            draw.text((80 + col_w, row_y + 30), f"Rp {sell_price:,.0f}", fill=text_primary, font=font_value)
            
            draw.text((80, row_y + step_y), "HOLDING TIME", fill=text_secondary, font=font_label)
            draw.text((80, row_y + step_y + 30), f"{holding_days} Days", fill=text_primary, font=font_value)
            draw.text((80 + col_w, row_y + step_y), "NET REALIZED VALUE", fill=text_secondary, font=font_label)
            draw.text((80 + col_w, row_y + step_y + 30), f"Rp {realized_pl:+,.0f}", fill=accent_color, font=font_value)
            
            draw.text((80, row_y + 2*step_y), "SIGNAL SETUP AT BUY", fill=text_secondary, font=font_label)
            draw.text((80, row_y + 2*step_y + 30), f"Final Score: {final_score} (T:{tech_score}/F:{flow_score})", fill=text_primary, font=font_value)
            draw.text((80 + col_w, row_y + 2*step_y), "EXIT STRATEGY", fill=text_secondary, font=font_label)
            draw.text((80 + col_w, row_y + 2*step_y + 30), exit_type, fill=text_primary, font=font_value)
            
        else:
            # Standard detailed grid of metrics (3 columns x 3 rows)
            col_w = 310
            row_y = 400
            step_y = 130
            
            # Row 1
            draw.text((80, row_y), "BUY PRICE", fill=text_secondary, font=font_label)
            draw.text((80, row_y + 30), f"Rp {buy_price:,.0f}", fill=text_primary, font=font_value)
            
            draw.text((80 + col_w, row_y), "SELL PRICE", fill=text_secondary, font=font_label)
            draw.text((80 + col_w, row_y + 30), f"Rp {sell_price:,.0f}", fill=text_primary, font=font_value)
            
            draw.text((80 + 2*col_w, row_y), "REALIZED P/L", fill=text_secondary, font=font_label)
            draw.text((80 + 2*col_w, row_y + 30), f"Rp {realized_pl:+,.0f}", fill=accent_color, font=font_value)
            
            # Row 2
            draw.text((80, row_y + step_y), "HOLDING TIME", fill=text_secondary, font=font_label)
            draw.text((80, row_y + step_y + 30), f"{holding_days} Days", fill=text_primary, font=font_value)
            
            draw.text((80 + col_w, row_y + step_y), "TP1 / TP2 TARGET", fill=text_secondary, font=font_label)
            draw.text((80 + col_w, row_y + step_y + 30), f"Rp {tp1:,.0f} / Rp {tp2:,.0f}" if (tp1 and tp2) else "N/A", fill=text_primary, font=font_value_sm)
            
            draw.text((80 + 2*col_w, row_y + step_y), "STOP LOSS LIMIT", fill=text_secondary, font=font_label)
            draw.text((80 + 2*col_w, row_y + step_y + 30), f"Rp {sl:,.0f}" if sl else "N/A", fill=text_primary, font=font_value)
            
            # Row 3
            draw.text((80, row_y + 2*step_y), "TP1 / TP2 HIT", fill=text_secondary, font=font_label)
            draw.text((80, row_y + 2*step_y + 30), f"{tp1_hit} / {tp2_hit}", fill=text_primary, font=font_value)
            
            draw.text((80 + col_w, row_y + 2*step_y), "SL HIT", fill=text_secondary, font=font_label)
            draw.text((80 + col_w, row_y + 2*step_y + 30), sl_hit, fill=text_primary, font=font_value)
            
            draw.text((80 + 2*col_w, row_y + 2*step_y), "MAX GAIN / DD", fill=text_secondary, font=font_label)
            draw.text((80 + 2*col_w, row_y + 2*step_y + 30), f"{max_gain:+.1f}% / {max_dd:+.1f}%", fill=text_primary, font=font_value_sm)
            
            # Row 4: Score summary & Reason
            draw.line([80, row_y + 3*step_y, width - 80, row_y + 3*step_y], fill=divider_color, width=1)
            
            draw.text((80, row_y + 3*step_y + 20), "TECHNICAL SCORE", fill=text_secondary, font=font_label)
            draw.text((80, row_y + 3*step_y + 50), f"{tech_score}/100", fill=text_primary, font=font_value)
            
            draw.text((80 + col_w, row_y + 3*step_y + 20), "FLOW SCORE", fill=text_secondary, font=font_label)
            draw.text((80 + col_w, row_y + 3*step_y + 50), f"{flow_score}/100", fill=text_primary, font=font_value)
            
            draw.text((80 + 2*col_w, row_y + 3*step_y + 20), "MAIN REASON", fill=text_secondary, font=font_label)
            wrapped_reason = reason[:30] + "..." if len(reason) > 30 else reason
            draw.text((80 + 2*col_w, row_y + 3*step_y + 50), wrapped_reason, fill=text_primary, font=font_value_sm)
            
        # Footer (Unified for square feed)
        draw.line([80, height - 140, width - 80, height - 140], fill=divider_color, width=2)
        draw.text((80, height - 100), "For tracking & evaluation only. Not financial advice.", fill=text_muted, font=font_footer)
        draw.text((width - 320, height - 100), f"Generated: {datetime.now().strftime('%Y-%m-%d')}", fill=text_muted, font=font_footer)

    # 5. Output Byte Stream
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
