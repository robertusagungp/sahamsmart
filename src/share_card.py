import os
import io
import urllib.request
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

def get_custom_font(size, bold=False):
    """
    Bulletproof self-healing font loader.
    If local TrueType fonts are not found, downloads Roboto from Google Fonts CDN to ensure
    high-quality, large typography rendering on any system (Windows, Linux, Streamlit Cloud).
    """
    font_dir = "data/fonts"
    os.makedirs(font_dir, exist_ok=True)
    
    font_name = "Roboto-Bold.ttf" if bold else "Roboto-Regular.ttf"
    font_path = os.path.join(font_dir, font_name)
    
    # 1. Try to download if not exists
    if not os.path.exists(font_path):
        try:
            url = f"https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/{font_name}"
            # Use Request with User-Agent to bypass GitHub's default script blocking
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            with urllib.request.urlopen(req, timeout=10) as response, open(font_path, 'wb') as out_file:
                out_file.write(response.read())
        except Exception as e:
            print(f"Warning: Failed to download custom font: {str(e)}")
            
    # 2. Try to load downloaded font
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception as e:
            print(f"Warning: Failed to load downloaded font: {str(e)}")
            
    # 3. Fallback to OS paths
    font_paths = [
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
                
    # 4. Final fallback (Will ignore size, but won't crash)
    return ImageFont.load_default()

def generate_share_card(trade_data: dict, template: str = "Formal Dark", size_ratio: str = "1080x1080") -> io.BytesIO:
    """
    Generates a stunning, premium trading share card with a modern widget-card grid composition.
    Maximizes text visibility by wrapping metrics inside individual card widgets.
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
    raw_signal = str(trade_data.get("app_signal_at_buy", "BUY"))
    if raw_signal in ["Watchlist Prioritas", "BUY"]:
        app_signal = "Watchlist Prioritas"
    elif raw_signal in ["Wait and See", "HOLD", "WATCH", "HOLD / WATCH"]:
        app_signal = "Wait and See"
    else:
        app_signal = "Keluar dari Watchlist"
    
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
        divider_color = "#f1f5f9" # box bg color
        box_border = "#e2e8f0"
    elif is_exec:
        bg_canvas = "#09090b"
        bg_card = "#18181b"
        border_color = "#27272a"
        text_primary = "#ffffff"
        text_secondary = "#a3a3a3"
        text_muted = "#525252"
        divider_color = "#27272a" # box bg color
        box_border = "#3f3f46"
    else: # Formal Dark
        bg_canvas = "#0d0e12"
        bg_card = "#16171e"
        border_color = accent_color # Glowing accent border
        text_primary = "#ffffff"
        text_secondary = "#94a3b8"
        text_muted = "#4b5563"
        divider_color = "#22242f" # box bg color
        box_border = "#2e303f"

    # Font Setup (Large Scale for high visibility)
    font_title = get_custom_font(34, bold=True)
    font_ticker = get_custom_font(110, bold=True)
    font_roi = get_custom_font(84, bold=True)
    font_label = get_custom_font(18, bold=False)
    font_value = get_custom_font(26, bold=True)
    font_value_sm = get_custom_font(22, bold=True)
    font_footer = get_custom_font(18, bold=False)
    
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
    draw.line([90, 165, width - 90, 165], fill=box_border, width=2)
    
    # 4. ASPECT RATIO LAYOUT DRAWERS WITH WIDGET BOXES
    if size_ratio == "1200x628": # TELEGRAM PREVIEW (Wide Landscape)
        draw.text((90, 185), ticker, fill=text_primary, font=font_ticker)
        
        # Outcome status label
        draw.rounded_rectangle([390, 195, 530, 230], radius=6, fill=accent_bg)
        draw.text((405, 203), status_label, fill=accent_color, font=get_custom_font(14, bold=True))
        
        # Giant ROI Badge
        roi_text = f"{roi:+.2f}%"
        draw.rounded_rectangle([560, 180, 890, 290], radius=16, fill=accent_color)
        draw.text((590, 185), roi_text, fill="#ffffff", font=get_custom_font(80, bold=True))
        
        # Signal tag
        draw.rounded_rectangle([90, 305, 280, 340], radius=6, fill=divider_color)
        draw.text((105, 313), f"Signal at Buy: {app_signal}", fill=text_secondary, font=get_custom_font(14, bold=True))
        
        # Grid of 4 cols x 2 rows
        col_w = 230
        row_h = 100
        x_gap = 30
        y_gap = 20
        start_y = 370
        
        metrics = [
            ("BUY PRICE", f"Rp {buy_price:,.0f}", text_secondary, text_primary),
            ("HOLDING TIME", f"{holding_days} Days", text_secondary, text_primary),
            ("TP1 / TP2 HIT", f"{tp1_hit} / {tp2_hit}", text_secondary, text_primary),
            ("MAX GAIN / DD", f"{max_gain:+.1f}% / {max_dd:+.1f}%", text_secondary, text_primary),
            ("SELL PRICE", f"Rp {sell_price:,.0f}", text_secondary, text_primary),
            ("REALIZED P/L", f"Rp {realized_pl:+,.0f}", text_secondary, accent_color),
            ("SL HIT", sl_hit, text_secondary, text_primary),
            ("FINAL SCORE", f"{final_score:.1f}", text_secondary, text_primary)
        ]
        
        for idx, (lbl, val, lbl_col, val_col) in enumerate(metrics):
            c_idx = idx % 4
            r_idx = idx // 4
            x1 = 90 + c_idx * (col_w + x_gap)
            y1 = start_y + r_idx * (row_h + y_gap)
            x2 = x1 + col_w
            y2 = y1 + row_h
            
            draw.rounded_rectangle([x1, y1, x2, y2], radius=12, fill=divider_color, outline=box_border, width=1)
            
            # Draw Centered Label
            lbl_font = get_custom_font(14, bold=False)
            lbl_w = draw.textlength(lbl, font=lbl_font)
            draw.text((x1 + (col_w - lbl_w)/2, y1 + 18), lbl, fill=lbl_col, font=lbl_font)
            
            # Draw Centered Value
            val_font = get_custom_font(18, bold=True)
            val_w = draw.textlength(val, font=val_font)
            draw.text((x1 + (col_w - val_w)/2, y1 + 48), val, fill=val_col, font=val_font)
            
        # Footer
        draw.line([90, 560, width - 90, 560], fill=box_border, width=1)
        draw.text((90, 578), "For tracking & evaluation only. Not financial advice.", fill=text_muted, font=font_footer)
        draw.text((width - 340, 578), f"Generated: {datetime.now().strftime('%Y-%m-%d')}", fill=text_muted, font=font_footer)

    elif size_ratio == "1080x1920": # INSTAGRAM STORY (Vertical)
        draw.text((90, 220), ticker, fill=text_primary, font=font_ticker)
        
        # Giant ROI Banner
        draw.rounded_rectangle([90, 360, width - 90, 540], radius=24, fill=accent_color)
        roi_text = f"{roi:+.2f}%"
        draw.text((130, 400), roi_text, fill="#ffffff", font=get_custom_font(96, bold=True))
        
        # Tags Row
        draw.rounded_rectangle([90, 580, 280, 620], radius=8, fill=accent_bg)
        draw.text((105, 590), f"RESULT: {status_label}", fill=accent_color, font=get_custom_font(16, bold=True))
        
        draw.rounded_rectangle([310, 580, 550, 620], radius=8, fill=divider_color)
        draw.text((325, 590), f"SIGNAL: {app_signal} (Sc: {final_score})", fill=text_secondary, font=get_custom_font(16, bold=True))
        
        draw.line([90, 660, width - 90, 660], fill=box_border, width=2)
        
        # 2 Columns x 5 Rows Grid
        col_w = 430
        row_h = 150
        x_gap = 40
        y_gap = 30
        start_y = 700
        
        metrics = [
            ("BUY PRICE", f"Rp {buy_price:,.0f} ({buy_date})", text_secondary, text_primary),
            ("SELL PRICE", f"Rp {sell_price:,.0f} ({sell_date})", text_secondary, text_primary),
            ("NET REALIZED P/L", f"Rp {realized_pl:+,.0f}", text_secondary, accent_color),
            ("HOLDING PERIOD", f"{holding_days} Days", text_secondary, text_primary),
            ("TP1 / TP2 TARGET", f"Rp {tp1:,.0f} / Rp {tp2:,.0f}" if (tp1 and tp2) else "N/A", text_secondary, text_primary),
            ("STOP LOSS LIMIT", f"Rp {sl:,.0f}" if sl else "N/A", text_secondary, text_primary),
            ("TP1 / TP2 HITS", f"{tp1_hit} / {tp2_hit}", text_secondary, text_primary),
            ("STOP LOSS HIT", sl_hit, text_secondary, text_primary),
            ("MAX GAIN AFTER BUY", f"{max_gain:+.2f}%", text_secondary, "#10b981"),
            ("MAX DRAWDOWN AFTER BUY", f"{max_dd:+.2f}%", text_secondary, "#ef4444")
        ]
        
        for idx, (lbl, val, lbl_col, val_col) in enumerate(metrics):
            c_idx = idx % 2
            r_idx = idx // 2
            x1 = 90 + c_idx * (col_w + x_gap)
            y1 = start_y + r_idx * (row_h + y_gap)
            x2 = x1 + col_w
            y2 = y1 + row_h
            
            draw.rounded_rectangle([x1, y1, x2, y2], radius=16, fill=divider_color, outline=box_border, width=1)
            
            lbl_font = get_custom_font(16, bold=False)
            lbl_w = draw.textlength(lbl, font=lbl_font)
            draw.text((x1 + (col_w - lbl_w)/2, y1 + 25), lbl, fill=lbl_col, font=lbl_font)
            
            val_font = get_custom_font(22, bold=True)
            if len(val) > 22:
                val_font = get_custom_font(16, bold=True)
            val_w = draw.textlength(val, font=val_font)
            draw.text((x1 + (col_w - val_w)/2, y1 + 75), val, fill=val_col, font=val_font)
            
        # Entry Reason full-width box at the bottom
        reason_box_y1 = start_y + 5 * (row_h + y_gap)
        reason_box_y2 = reason_box_y1 + 130
        draw.rounded_rectangle([90, reason_box_y1, width - 90, reason_box_y2], radius=16, fill=divider_color, outline=box_border, width=1)
        
        lbl_font = get_custom_font(16, bold=False)
        draw.text((120, reason_box_y1 + 20), "MAIN ENTRY REASON", fill=text_secondary, font=lbl_font)
        wrapped_reason = reason[:85] + "..." if len(reason) > 85 else reason
        draw.text((120, reason_box_y1 + 60), wrapped_reason, fill=text_primary, font=get_custom_font(20, bold=True))
        
        # Footer
        draw.line([90, height - 160, width - 90, height - 160], fill=box_border, width=2)
        draw.text((90, height - 120), "For tracking & evaluation only. Not financial advice.", fill=text_muted, font=font_footer)
        draw.text((width - 340, height - 120), f"Generated: {datetime.now().strftime('%Y-%m-%d')}", fill=text_muted, font=font_footer)

    else: # 1080x1080 INSTAGRAM FEED (Square Grid)
        # Ticker Left
        draw.text((90, 190), ticker, fill=text_primary, font=font_ticker)
        
        # Tags under Ticker
        draw.rounded_rectangle([90, 305, 250, 340], radius=6, fill=accent_bg)
        draw.text((105, 313), status_label, fill=accent_color, font=get_custom_font(14, bold=True))
        
        draw.rounded_rectangle([280, 305, 490, 340], radius=6, fill=divider_color)
        draw.text((295, 313), f"Signal: {app_signal} (Sc: {final_score})", fill=text_secondary, font=get_custom_font(14, bold=True))
        
        # Giant ROI Badge Right
        draw.rounded_rectangle([520, 185, width - 90, 335], radius=20, fill=accent_color)
        roi_text = f"{roi:+.2f}%"
        draw.text((560, 205), roi_text, fill="#ffffff", font=font_roi)
        draw.text((560, 290), "REALIZED RETURN (ROI)", fill="#f1f5f9", font=get_custom_font(15, bold=True))
        
        draw.line([90, 380, width - 90, 380], fill=box_border, width=2)
        
        # Grid of 3 Columns x 3 Rows
        margin_left = 90
        col_w = 280
        row_h = 135
        x_gap = 30
        y_gap = 25
        start_y = 410
        
        if is_exec:
            metrics = [
                ("BUY PRICE", f"Rp {buy_price:,.0f}", text_secondary, text_primary),
                ("SELL PRICE", f"Rp {sell_price:,.0f}", text_secondary, text_primary),
                ("NET REALIZED VALUE", f"Rp {realized_pl:+,.0f}", text_secondary, accent_color),
                ("HOLDING TIME", f"{holding_days} Days", text_secondary, text_primary),
                ("INITIAL SIGNAL", app_signal, text_secondary, tag_fg),
                ("FINAL SCORE", f"{final_score:.1f}", text_secondary, text_primary),
                ("TECHNICAL SCORE", f"{tech_score}/100", text_secondary, text_primary),
                ("FLOW SCORE", f"{flow_score}/100", text_secondary, text_primary),
                ("EXIT STRATEGY", exit_type, text_secondary, "#f59e0b")
            ]
        else:
            metrics = [
                ("BUY PRICE", f"Rp {buy_price:,.0f}", text_secondary, text_primary),
                ("SELL PRICE", f"Rp {sell_price:,.0f}", text_secondary, text_primary),
                ("REALIZED P/L", f"Rp {realized_pl:+,.0f}", text_secondary, accent_color),
                ("HOLDING TIME", f"{holding_days} Days", text_secondary, text_primary),
                ("TP1 / TP2 TARGET", f"Rp {tp1:,.0f} / Rp {tp2:,.0f}" if (tp1 and tp2) else "N/A", text_secondary, text_primary),
                ("STOP LOSS LIMIT", f"Rp {sl:,.0f}" if sl else "N/A", text_secondary, text_primary),
                ("TP1 / TP2 HIT", f"{tp1_hit} / {tp2_hit}", text_secondary, text_primary),
                ("SL HIT", sl_hit, text_secondary, text_primary),
                ("MAX GAIN / DD", f"{max_gain:+.1f}% / {max_dd:+.1f}%", text_secondary, text_primary)
            ]
            
        for idx, (lbl, val, lbl_col, val_col) in enumerate(metrics):
            c_idx = idx % 3
            r_idx = idx // 3
            
            x1 = margin_left + c_idx * (col_w + x_gap)
            y1 = start_y + r_idx * (row_h + y_gap)
            x2 = x1 + col_w
            y2 = y1 + row_h
            
            draw.rounded_rectangle([x1, y1, x2, y2], radius=16, fill=divider_color, outline=box_border, width=1)
            
            # Center Label
            lbl_font = get_custom_font(15, bold=False)
            lbl_w = draw.textlength(lbl, font=lbl_font)
            draw.text((x1 + (col_w - lbl_w)/2, y1 + 25), lbl, fill=lbl_col, font=lbl_font)
            
            # Center Value
            val_font = get_custom_font(22, bold=True)
            if len(val) > 20:
                val_font = get_custom_font(15, bold=True)
            elif len(val) > 15:
                val_font = get_custom_font(18, bold=True)
            val_w = draw.textlength(val, font=val_font)
            draw.text((x1 + (col_w - val_w)/2, y1 + 65), val, fill=val_col, font=val_font)
            
        # Footer
        draw.line([90, height - 140, width - 90, height - 140], fill=box_border, width=2)
        draw.text((90, height - 100), "For tracking & evaluation only. Not financial advice.", fill=text_muted, font=font_footer)
        draw.text((width - 340, height - 100), f"Generated: {datetime.now().strftime('%Y-%m-%d')}", fill=text_muted, font=font_footer)

    # 5. Save and Return Byte Stream
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
