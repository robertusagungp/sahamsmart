import os
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

def generate_share_card(trade_data: dict, template: str = "Formal Dark", size_ratio: str = "1080x1080") -> io.BytesIO:
    """
    Generates a stunning, premium trading share card with focus on giant ROI typography.
    Supports Formal Light, Formal Dark, and Executive Summary templates across 3 aspect ratios.
    """
    # 1. Dimensions Setup
    if size_ratio == "1080x1920":
        width, height = 1080, 1920
    elif size_ratio == "1200x628":
        width, height = 1200, 628
    else:
        width, height = 1080, 1080
        
    # 2. Color Palettes
    is_light = template == "Formal Light"
    is_exec = template == "Executive Summary"
    
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
    
    # Establish Win/Loss status
    if roi >= 0.0:
        status_label = "PROFIT"
        accent_color = "#10b981" # Emerald Green
        accent_bg = "#064e3b"
        tag_bg = "#064e3b"
        tag_fg = "#34d399"
    else:
        status_label = "LOSS"
        accent_color = "#ef4444" # Ruby Red
        accent_bg = "#7f1d1d"
        tag_bg = "#7f1d1d"
        tag_fg = "#f87171"

    if is_light:
        bg_canvas = "#f1f5f9"
        bg_card = "#ffffff"
        border_color = accent_color # Glowing border
        text_primary = "#0f172a"
        text_secondary = "#475569"
        text_muted = "#94a3b8"
        divider_color = "#e2e8f0"
    elif is_exec:
        bg_canvas = "#09090b"
        bg_card = "#18181b"
        border_color = "#27272a"
        text_primary = "#ffffff"
        text_secondary = "#a3a3a3"
        text_muted = "#525252"
        divider_color = "#27272a"
    else: # Formal Dark
        bg_canvas = "#0d0e12"
        bg_card = "#16171e"
        border_color = accent_color # Glowing accent border
        text_primary = "#ffffff"
        text_secondary = "#94a3b8"
        text_muted = "#4b5563"
        divider_color = "#2e303f"

    # Font Setup (Large Scale for high visibility)
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

    font_title = get_font(34, bold=True)
    font_ticker = get_font(110, bold=True)
    font_roi = get_font(100, bold=True) # Huge ROI
    font_label = get_font(20, bold=False)
    font_value = get_font(28, bold=True)
    font_value_sm = get_font(23, bold=True)
    font_footer = get_font(18, bold=False)
    
    # 3. Canvas Painting
    img = Image.new("RGBA", (width, height), bg_canvas)
    draw = ImageDraw.Draw(img)
    
    # Draw central rounded container card
    margin_x, margin_y = 40, 40
    draw.rounded_rectangle(
        [margin_x, margin_y, width - margin_x, height - margin_y],
        radius=30, fill=bg_card, outline=border_color, width=4
    )
    
    # Highlight stripe for Executive Summary
    if is_exec:
        draw.rounded_rectangle(
            [margin_x, margin_y, margin_x + 18, height - margin_y],
            radius=10, fill=accent_color
        )
        
    # Draw Header (Smart Saham Premium)
    draw.text((90, 85), "👑 Smart Saham Premium", fill="#f59e0b", font=font_title)
    draw.text((90, 130), f"CLOSED TRADE EXIT REPORT  •  {sell_date}", fill=text_secondary, font=font_label)
    draw.line([90, 165, width - 90, 165], fill=divider_color, width=2)
    
    # 4. ASPECT RATIO LAYOUT DRAWERS
    if size_ratio == "1200x628": # TELEGRAM PREVIEW (Wide Landscape)
        # Ticker & ROI Side-by-Side
        draw.text((90, 185), ticker, fill=text_primary, font=font_ticker)
        
        # Outcome status label
        draw.rounded_rectangle([390, 195, 530, 230], radius=6, fill=accent_bg)
        draw.text((405, 203), status_label, fill=accent_color, font=get_font(14, bold=True))
        
        # Giant ROI Badge
        roi_text = f"{roi:+.2f}%"
        draw.rounded_rectangle([560, 180, 890, 290], radius=16, fill=accent_color)
        draw.text((590, 185), roi_text, fill="#ffffff", font=get_font(80, bold=True))
        
        # Signal tag
        draw.rounded_rectangle([90, 310, 280, 345], radius=6, fill=divider_color)
        draw.text((105, 318), f"Signal at Buy: {app_signal}", fill=text_secondary, font=get_font(14, bold=True))
        
        # Grid layout (4 cols x 2 rows)
        col_w = 260
        row1_y = 385
        row2_y = 485
        
        # Col 0
        draw.text((90, row1_y), "BUY PRICE", fill=text_secondary, font=font_label)
        draw.text((90, row1_y + 30), f"Rp {buy_price:,.0f}", fill=text_primary, font=font_value)
        draw.text((90, row2_y), "SELL PRICE", fill=text_secondary, font=font_label)
        draw.text((90, row2_y + 30), f"Rp {sell_price:,.0f}", fill=text_primary, font=font_value)
        
        # Col 1
        draw.text((90 + col_w, row1_y), "HOLDING TIME", fill=text_secondary, font=font_label)
        draw.text((90 + col_w, row1_y + 30), f"{holding_days} Days", fill=text_primary, font=font_value)
        draw.text((90 + col_w, row2_y), "REALIZED P/L", fill=text_secondary, font=font_label)
        draw.text((90 + col_w, row2_y + 30), f"Rp {realized_pl:+,.0f}", fill=accent_color, font=font_value)
        
        # Col 2
        draw.text((90 + 2*col_w, row1_y), "TP1 / TP2 HIT", fill=text_secondary, font=font_label)
        draw.text((90 + 2*col_w, row1_y + 30), f"{tp1_hit} / {tp2_hit}", fill=text_primary, font=font_value)
        draw.text((90 + 2*col_w, row2_y), "SL HIT", fill=text_secondary, font=font_label)
        draw.text((90 + 2*col_w, row2_y + 30), sl_hit, fill=text_primary, font=font_value)
        
        # Col 3
        draw.text((90 + 3*col_w, row1_y), "MAX GAIN / DD", fill=text_secondary, font=font_label)
        draw.text((90 + 3*col_w, row1_y + 30), f"{max_gain:+.1f}% / {max_dd:+.1f}%", fill=text_primary, font=font_value_sm)
        draw.text((90 + 3*col_w, row2_y), "FINAL SCORE", fill=text_secondary, font=font_label)
        draw.text((90 + 3*col_w, row2_y + 30), f"{final_score} (T:{tech_score}/F:{flow_score})", fill=text_primary, font=font_value_sm)
        
        # Footer
        draw.line([90, 560, width - 90, 560], fill=divider_color, width=1)
        draw.text((90, 578), "For tracking & evaluation only. Not financial advice.", fill=text_muted, font=font_footer)
        draw.text((width - 340, 578), f"Generated: {datetime.now().strftime('%Y-%m-%d')}", fill=text_muted, font=font_footer)

    elif size_ratio == "1080x1920": # INSTAGRAM STORY (Portrait)
        # Giant Ticker
        draw.text((90, 220), ticker, fill=text_primary, font=font_ticker)
        
        # Massive Centered ROI Banner
        draw.rounded_rectangle([90, 360, width - 90, 540], radius=24, fill=accent_color)
        roi_text = f"{roi:+.2f}%"
        draw.text((130, 400), roi_text, fill="#ffffff", font=get_font(96, bold=True))
        
        # Tags Row
        draw.rounded_rectangle([90, 580, 280, 620], radius=8, fill=accent_bg)
        draw.text((105, 590), f"RESULT: {status_label}", fill=accent_color, font=get_font(16, bold=True))
        
        draw.rounded_rectangle([310, 580, 550, 620], radius=8, fill=divider_color)
        draw.text((325, 590), f"SIGNAL: {app_signal} (Sc: {final_score})", fill=text_secondary, font=get_font(16, bold=True))
        
        draw.line([90, 660, width - 90, 660], fill=divider_color, width=2)
        
        # Grid Parameters (2 Columns)
        col_w = 460
        row_y = 700
        step_y = 150
        
        # Row 1
        draw.text((90, row_y), "BUY PRICE", fill=text_secondary, font=font_label)
        draw.text((90, row_y + 35), f"Rp {buy_price:,.0f} ({buy_date})", fill=text_primary, font=font_value)
        draw.text((90 + col_w, row_y), "SELL PRICE", fill=text_secondary, font=font_label)
        draw.text((90 + col_w, row_y + 35), f"Rp {sell_price:,.0f} ({sell_date})", fill=text_primary, font=font_value)
        
        # Row 2
        draw.text((90, row_y + step_y), "NET REALIZED P/L", fill=text_secondary, font=font_label)
        draw.text((90, row_y + step_y + 35), f"Rp {realized_pl:+,.0f}", fill=accent_color, font=font_value)
        draw.text((90 + col_w, row_y + step_y), "HOLDING PERIOD", fill=text_secondary, font=font_label)
        draw.text((90 + col_w, row_y + step_y + 35), f"{holding_days} Days", fill=text_primary, font=font_value)
        
        # Row 3
        draw.text((90, row_y + 2*step_y), "TP1 / TP2 TARGET", fill=text_secondary, font=font_label)
        draw.text((90, row_y + 2*step_y + 35), f"Rp {tp1:,.0f} / Rp {tp2:,.0f}" if (tp1 and tp2) else "N/A", fill=text_primary, font=font_value_sm)
        draw.text((90 + col_w, row_y + 2*step_y), "STOP LOSS LIMIT", fill=text_secondary, font=font_label)
        draw.text((90 + col_w, row_y + 2*step_y + 35), f"Rp {sl:,.0f}" if sl else "N/A", fill=text_primary, font=font_value)
        
        # Row 4
        draw.text((90, row_y + 3*step_y), "TP1 / TP2 HITS", fill=text_secondary, font=font_label)
        draw.text((90, row_y + 3*step_y + 35), f"{tp1_hit} / {tp2_hit}", fill=text_primary, font=font_value)
        draw.text((90 + col_w, row_y + 3*step_y), "STOP LOSS HIT", fill=text_secondary, font=font_label)
        draw.text((90 + col_w, row_y + 3*step_y + 35), sl_hit, fill=text_primary, font=font_value)
        
        # Row 5
        draw.text((90, row_y + 4*step_y), "MAX GAIN AFTER BUY", fill=text_secondary, font=font_label)
        draw.text((90, row_y + 4*step_y + 35), f"{max_gain:+.2f}%", fill="#10b981", font=font_value)
        draw.text((90 + col_w, row_y + 4*step_y), "MAX DRAWDOWN AFTER BUY", fill=text_secondary, font=font_label)
        draw.text((90 + col_w, row_y + 4*step_y + 35), f"{max_dd:+.2f}%", fill="#ef4444", font=font_value)
        
        # Scores block
        draw.line([90, row_y + 5.1*step_y, width - 90, row_y + 5.1*step_y], fill=divider_color, width=1)
        draw.text((90, row_y + 5.3*step_y), "TECHNICAL SCORE", fill=text_secondary, font=font_label)
        draw.text((90, row_y + 5.3*step_y + 35), f"{tech_score}/100", fill=text_primary, font=font_value)
        draw.text((90 + col_w, row_y + 5.3*step_y), "FLOW SCORE", fill=text_secondary, font=font_label)
        draw.text((90 + col_w, row_y + 5.3*step_y + 35), f"{flow_score}/100", fill=text_primary, font=font_value)
        
        # Reasons
        draw.text((90, row_y + 6.5*step_y), "MAIN ENTRY REASON", fill=text_secondary, font=font_label)
        wrapped_reason = reason[:85] + "..." if len(reason) > 85 else reason
        draw.text((90, row_y + 6.5*step_y + 35), wrapped_reason, fill=text_primary, font=get_font(18, bold=False))
        
        # Footer
        draw.line([90, height - 160, width - 90, height - 160], fill=divider_color, width=2)
        draw.text((90, height - 120), "For tracking & evaluation only. Not financial advice.", fill=text_muted, font=font_footer)
        draw.text((width - 340, height - 120), f"Generated: {datetime.now().strftime('%Y-%m-%d')}", fill=text_muted, font=font_footer)

    else: # 1080x1080 INSTAGRAM FEED (Square)
        # Giant Ticker Left
        draw.text((90, 190), ticker, fill=text_primary, font=font_ticker)
        
        # Tags underneath ticker
        draw.rounded_rectangle([90, 305, 250, 340], radius=6, fill=accent_bg)
        draw.text((105, 313), status_label, fill=accent_color, font=get_font(14, bold=True))
        
        draw.rounded_rectangle([280, 305, 490, 340], radius=6, fill=divider_color)
        draw.text((295, 313), f"Signal: {app_signal} (Sc: {final_score})", fill=text_secondary, font=get_font(14, bold=True))
        
        # Huge ROI Badge Right
        draw.rounded_rectangle([520, 185, width - 90, 335], radius=20, fill=accent_color)
        roi_text = f"{roi:+.2f}%"
        draw.text((560, 205), roi_text, fill="#ffffff", font=font_roi)
        draw.text((560, 290), "REALIZED RETURN (ROI)", fill="#f1f5f9", font=get_font(15, bold=True))
        
        draw.line([90, 380, width - 90, 380], fill=divider_color, width=2)
        
        if is_exec:
            # Executive Summary Layout Grid (2 cols x 3 rows)
            col_w = 460
            row_y = 430
            step_y = 150
            
            draw.text((90, row_y), "BUY PRICE", fill=text_secondary, font=font_label)
            draw.text((90, row_y + 35), f"Rp {buy_price:,.0f}", fill=text_primary, font=font_value)
            draw.text((90 + col_w, row_y), "SELL PRICE", fill=text_secondary, font=font_label)
            draw.text((90 + col_w, row_y + 35), f"Rp {sell_price:,.0f}", fill=text_primary, font=font_value)
            
            draw.text((90, row_y + step_y), "HOLDING TIME", fill=text_secondary, font=font_label)
            draw.text((90, row_y + step_y + 35), f"{holding_days} Days", fill=text_primary, font=font_value)
            draw.text((90 + col_w, row_y + step_y), "NET REALIZED VALUE", fill=text_secondary, font=font_label)
            draw.text((90 + col_w, row_y + step_y + 35), f"Rp {realized_pl:+,.0f}", fill=accent_color, font=font_value)
            
            draw.text((90, row_y + 2*step_y), "SIGNAL SETUP AT BUY", fill=text_secondary, font=font_label)
            draw.text((90, row_y + 2*step_y + 35), f"Final Score: {final_score} (T:{tech_score}/F:{flow_score})", fill=text_primary, font=font_value)
            draw.text((90 + col_w, row_y + 2*step_y), "EXIT STRATEGY", fill=text_secondary, font=font_label)
            draw.text((90 + col_w, row_y + 2*step_y + 35), exit_type, fill=text_primary, font=font_value)
            
        else:
            # Full grid (3 Columns x 3 rows)
            col_w = 310
            row_y = 415
            step_y = 135
            
            # Row 1
            draw.text((90, row_y), "BUY PRICE", fill=text_secondary, font=font_label)
            draw.text((90, row_y + 35), f"Rp {buy_price:,.0f}", fill=text_primary, font=font_value)
            draw.text((90 + col_w, row_y), "SELL PRICE", fill=text_secondary, font=font_label)
            draw.text((90 + col_w, row_y + 35), f"Rp {sell_price:,.0f}", fill=text_primary, font=font_value)
            draw.text((90 + 2*col_w, row_y), "REALIZED P/L", fill=text_secondary, font=font_label)
            draw.text((90 + 2*col_w, row_y + 35), f"Rp {realized_pl:+,.0f}", fill=accent_color, font=font_value)
            
            # Row 2
            draw.text((90, row_y + step_y), "HOLDING TIME", fill=text_secondary, font=font_label)
            draw.text((90, row_y + step_y + 35), f"{holding_days} Days", fill=text_primary, font=font_value)
            draw.text((90 + col_w, row_y + step_y), "TP1 / TP2 TARGET", fill=text_secondary, font=font_label)
            draw.text((90 + col_w, row_y + step_y + 35), f"Rp {tp1:,.0f} / Rp {tp2:,.0f}" if (tp1 and tp2) else "N/A", fill=text_primary, font=font_value_sm)
            draw.text((90 + 2*col_w, row_y + step_y), "STOP LOSS LIMIT", fill=text_secondary, font=font_label)
            draw.text((90 + 2*col_w, row_y + step_y + 35), f"Rp {sl:,.0f}" if sl else "N/A", fill=text_primary, font=font_value)
            
            # Row 3
            draw.text((90, row_y + 2*step_y), "TP1 / TP2 HITS", fill=text_secondary, font=font_label)
            draw.text((90, row_y + 2*step_y + 35), f"{tp1_hit} / {tp2_hit}", fill=text_primary, font=font_value)
            draw.text((90 + col_w, row_y + 2*step_y), "STOP LOSS HIT", fill=text_secondary, font=font_label)
            draw.text((90 + col_w, row_y + 2*step_y + 35), sl_hit, fill=text_primary, font=font_value)
            draw.text((90 + 2*col_w, row_y + 2*step_y), "MAX GAIN / DD", fill=text_secondary, font=font_label)
            draw.text((90 + 2*col_w, row_y + 2*step_y + 35), f"{max_gain:+.1f}% / {max_dd:+.1f}%", fill=text_primary, font=font_value_sm)
            
            # Row 4: Score details & Reason
            draw.line([90, row_y + 3*step_y, width - 90, row_y + 3*step_y], fill=divider_color, width=1)
            
            draw.text((90, row_y + 3*step_y + 20), "TECHNICAL SCORE", fill=text_secondary, font=font_label)
            draw.text((90, row_y + 3*step_y + 50), f"{tech_score}/100", fill=text_primary, font=font_value)
            
            draw.text((90 + col_w, row_y + 3*step_y + 20), "FLOW SCORE", fill=text_secondary, font=font_label)
            draw.text((90 + col_w, row_y + 3*step_y + 50), f"{flow_score}/100", fill=text_primary, font=font_value)
            
            draw.text((90 + 2*col_w, row_y + 3*step_y + 20), "MAIN REASON", fill=text_secondary, font=font_label)
            wrapped_reason = reason[:30] + "..." if len(reason) > 30 else reason
            draw.text((90 + 2*col_w, row_y + 3*step_y + 50), wrapped_reason, fill=text_primary, font=font_value_sm)
            
        # Footer (Unified for 1080x1080)
        draw.line([90, height - 140, width - 90, height - 140], fill=divider_color, width=2)
        draw.text((90, height - 100), "For tracking & evaluation only. Not financial advice.", fill=text_muted, font=font_footer)
        draw.text((width - 340, height - 100), f"Generated: {datetime.now().strftime('%Y-%m-%d')}", fill=text_muted, font=font_footer)

    # 5. Save and Return
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
