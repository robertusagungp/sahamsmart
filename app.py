import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, date
import os

# Import custom modules
from src.data_loader import StockDataLoader
from src.indicators import calculate_technical_indicators
from src.scoring import calculate_score
from src.storage import AnalysisStorage
from src.stock_list import get_all_idx_tickers, get_idx_stocks_df
from src.telegram_bot import send_telegram_alert

# Set page configuration with a modern title and wide layout
st.set_page_config(
    page_title="Smart Saham Premium - Portal Screening Saham IDX",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for glassmorphism styling, premium cards, login portal, and beautiful aesthetics
st.markdown("""
<style>
    /* Dark Theme Core Styles */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #1a1e29 0%, #0e1118 90%);
        color: #f8fafc;
    }
    
    /* Premium Glassmorphism Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }
    
    /* Login Portal Custom Styling */
    .login-container {
        max-width: 450px;
        margin: 60px auto;
        padding: 40px;
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 24px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 15px rgba(59, 130, 246, 0.2);
        text-align: center;
    }
    
    .login-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #1d4ed8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    .premium-badge {
        background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
        color: #1e1b4b;
        padding: 4px 12px;
        font-weight: 800;
        font-size: 0.75rem;
        border-radius: 12px;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 20px;
        letter-spacing: 1px;
    }

    /* Metric Grid Cards */
    .metric-grid-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 15px;
        text-align: center;
    }
    .metric-grid-val {
        font-size: 1.5rem;
        font-weight: 700;
        margin-top: 5px;
    }
    .metric-grid-lbl {
        font-size: 0.75rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Header Gradient Divider */
    .header-divider {
        height: 4px;
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #10b981 100%);
        margin-bottom: 25px;
        border-radius: 2px;
    }
    
    /* Signal Badges */
    .badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85rem;
        text-align: center;
        display: inline-block;
    }
    .badge-buy {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border: 1px solid #10b981;
    }
    .badge-watch {
        background-color: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
        border: 1px solid #f59e0b;
    }
    .badge-avoid {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid #ef4444;
    }
</style>
""", unsafe_allow_html=True)

# Initialize storage and loader modules
db_url = None
try:
    if "DATABASE_URL" in st.secrets:
        db_url = st.secrets["DATABASE_URL"]
except Exception:
    pass

if not db_url:
    db_url = os.environ.get("DATABASE_URL")

storage = AnalysisStorage(db_url=db_url)

def get_loader():
    return StockDataLoader()

loader = get_loader()

# Load all IDX stock tickers at startup
@st.cache_data(ttl=86400) # Cache listings for 24 hours
def load_stock_database():
    return get_all_idx_tickers()

@st.cache_data(ttl=86400) # Cache listings dataframe for 24 hours
def load_stock_database_df():
    return get_idx_stocks_df()

IDX_STOCKS = load_stock_database()

# ----------------- SESSION STATE & AUTHENTICATION MANAGEMENT -----------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# Render login/register page if not logged in
if not st.session_state["logged_in"]:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">💸 Smart Saham</div>', unsafe_allow_html=True)
    st.markdown('<div class="premium-badge">✨ PRO SCREENER PORTAL</div>', unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8; font-size:0.95rem; margin-top:-10px;'>Akses premium screening saham harian, visualisasi teknikal & histori log berbasis AI-Scoring</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Use Streamlit form layout for login UI
    login_tab, register_tab = st.tabs(["🔐 Masuk Ke Akun", "📝 Daftar Akun Baru"])
    
    with login_tab:
        col_c, col_d = st.columns([1, 1])
        with col_c:
            st.image("https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.0.3", use_container_width=True, caption="Pantau Momentum & Tren Saham Terbaik")
        with col_d:
            st.markdown("### Silakan Login")
            login_username = st.text_input("Username", key="login_u").strip()
            login_password = st.text_input("Password", type="password", key="login_p")
            submit_login = st.button("Masuk Sekarang 🚀", use_container_width=True)
            
            if submit_login:
                if storage.authenticate_user(login_username, login_password):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = login_username.lower()
                    # Log login activity
                    storage.log_activity(login_username, "LOGIN")
                    st.success("Login sukses! Membuka dashboard...")
                    st.rerun()
                else:
                    st.error("Username atau password salah. Coba lagi atau buat akun baru.")
                    
    with register_tab:
        col_e, col_f = st.columns([1, 1])
        with col_e:
            st.markdown("### Daftar Akun Premium")
            reg_username = st.text_input("Username Baru", key="reg_u").strip()
            reg_email = st.text_input("Email (Opsional)", key="reg_e").strip()
            reg_password = st.text_input("Password Baru", type="password", key="reg_p")
            reg_password_confirm = st.text_input("Konfirmasi Password", type="password", key="reg_pc")
            submit_register = st.button("Buat Akun Premium ✨", use_container_width=True)
            
            if submit_register:
                if not reg_username or not reg_password:
                    st.error("Username dan password tidak boleh kosong.")
                elif reg_password != reg_password_confirm:
                    st.error("Konfirmasi password tidak cocok.")
                else:
                    res = storage.create_user(reg_username, reg_password, reg_email)
                    if res["success"]:
                        st.success(res["message"])
                        # Log registration activity
                        storage.log_activity(reg_username, "REGISTER")
                    else:
                        st.error(res["message"])
        with col_f:
            st.markdown("""
            ### Benefit Akun Premium:
            - 📈 **Screener Saham Tak Terbatas**: Akses seluruh daftar saham di Bursa Efek Indonesia (IDX).
            - 🎯 **Advanced scoring system**: Kalkulasi momentum, volume trend, RSI, dan MA20/MA50.
            - 🛠️ **Dashboard detail & risiko**: Penjelasan alasan BUY / WATCH / AVOID beserta faktor risikonya.
            - 🗃️ **Sinkronisasi Database Awan**: Histori log tersinkronisasi di Neon DB (PostgreSQL).
            - 🔐 **Log Aktivitas Aman**: Seluruh tindakan terekam aman untuk audit analisis Anda.
            """)
    st.stop()

# ----------------- LOGGED IN APPLICATION INTERFACE -----------------

# Header area with Welcome message and Logout
col_header_title, col_header_user = st.columns([3, 1])
with col_header_title:
    st.title("👑 Smart Saham Premium Dashboard")
    st.markdown("##### *Sistem Screening & Analisis Keputusan Saham Indonesia Premium*")
with col_header_user:
    st.write("")
    st.markdown(f"👤 Akun: **{st.session_state['username'].upper()}** `[Premium Active]`")
    if st.button("🚪 Keluar Akun (Logout)", use_container_width=True):
        storage.log_activity(st.session_state["username"], "LOGOUT")
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.rerun()

st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)

# Create Sidebar configurations
with st.sidebar:
    st.header("⚙️ Konfigurasi Screener")
    
    # Sector and Custom presets in the sidebar
    selected_preset = st.selectbox(
        "🎯 Preset Kategori Saham:",
        options=[
            "Kustom (Pilih Manual)", 
            "Ketik Ticker Manual",
            "Semua Saham IDX (820+ Emiten)", 
            "Sektor Finansial (Financials)",
            "Sektor Energi (Energy)",
            "Sektor Teknologi (Technology)",
            "Sektor Infrastruktur (Infrastructure)",
            "Sektor Basic Materials",
            "Sektor Consumer Non-Cyclical",
            "Sektor Consumer Cyclical",
            "Sektor Healthcare",
            "Sektor Industrials",
            "Sektor Properties & Real Estate",
            "Sektor Transportation & Logistics"
        ]
    )
    
    selected_tickers = []
    
    if selected_preset == "Kustom (Pilih Manual)":
        # Multi-select using the dynamic IDX stock list
        selected_tickers = st.multiselect(
            "Pilih Saham (Bisa multi-select)",
            options=list(IDX_STOCKS.keys()),
            default=["BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK", "UNVR.JK", "GOTO.JK"],
            format_func=lambda x: f"{x.split('.')[0]} - {IDX_STOCKS.get(x, x)}"
        )
    elif selected_preset == "Ketik Ticker Manual":
        st.info("Ketik ticker saham Indonesia di bawah (pisahkan dengan koma jika lebih dari satu).")
        ticker_input = st.text_input("Contoh: BBNI, ANTM, PTBA", "BBNI, ANTM, PTBA")
        tickers_list = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
        formatted_tickers = []
        for t in tickers_list:
            if not t.endswith(".JK"):
                t = f"{t}.JK"
            formatted_tickers.append(t)
        selected_tickers = formatted_tickers
    elif selected_preset == "Semua Saham IDX (820+ Emiten)":
        selected_tickers = list(IDX_STOCKS.keys())
        st.warning("⚠️ Menganalisis 820+ saham sekaligus memerlukan waktu sekitar 1-2 menit. Klik tombol Refresh di bawah.")
    else:
        # Extract English name inside parenthesis if exists, otherwise use name directly
        sector_name = selected_preset.replace("Sektor ", "")
        if "(" in sector_name and ")" in sector_name:
            sector_name = sector_name.split("(")[1].split(")")[0]
        
        df_stocks_db = load_stock_database_df()
        df_sector = df_stocks_db[df_stocks_db['sector'] == sector_name]
        selected_tickers = df_sector['ticker'].tolist()
        st.info(f"Terpilih {len(selected_tickers)} saham di {selected_preset}.")
        
    st.write("")
    
    # Custom interactive addition box
    custom_add = st.text_input("Tambah Ticker Tambahan (Contoh: BRMS)", "")
    if custom_add:
        t_add = custom_add.strip().upper()
        if not t_add.endswith(".JK"):
            t_add = f"{t_add}.JK"
        if t_add not in selected_tickers:
            selected_tickers.append(t_add)

    # Rentang data historis
    history_period = st.selectbox(
        "Rentang Waktu Historis",
        options=["6mo", "1y", "2y"],
        index=1,
        help="Menentukan data historis yang ditarik dari yfinance."
    )
    
    st.markdown("---")
    st.markdown("🌐 **Database Sync Status**")
    if db_url:
        st.success("Terkoneksi ke Neon DB Cloud")
    else:
        st.info("Koneksi Database: Lokal (SQLite/CSV)")

    # Telegram Bot configuration expander in sidebar
    with st.expander("🔔 Konfigurasi Telegram Bot", expanded=False):
        st.write("Push alert sinyal saham langsung ke grup/channel Telegram Anda.")
        
        # Pull defaults from st.secrets if configured
        def_tg_token = ""
        def_tg_chat = ""
        try:
            def_tg_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
            def_tg_chat = st.secrets.get("TELEGRAM_CHAT_ID", "")
        except Exception:
            pass
            
        tg_bot_token = st.text_input("Bot Token", value=def_tg_token, type="password", help="API Token Bot Telegram Anda")
        tg_chat_id = st.text_input("Group/Chat ID", value=def_tg_chat, placeholder="Contoh: -100123456789", help="ID Grup/Channel dengan tanda (-) di depan")
        auto_send_buy = st.checkbox("Auto-Send Sinyal BUY", value=False, help="Kirim otomatis ke Telegram jika screening mendeteksi sinyal BUY")

    run_analysis = st.button("🔄 Jalankan & Simpan Analisis Baru", use_container_width=True)

# ----------------- CONTROLLER / STOCK PROCESSING PIPELINE -----------------

# Track selected tickers and period in session state to auto-run when changed
if "last_selected_tickers" not in st.session_state:
    st.session_state["last_selected_tickers"] = []
if "last_history_period" not in st.session_state:
    st.session_state["last_history_period"] = "1y"

tickers_changed = set(selected_tickers) != set(st.session_state["last_selected_tickers"])
period_changed = history_period != st.session_state["last_history_period"]

should_trigger = False
is_large_batch = len(selected_tickers) > 120

if "results" not in st.session_state:
    if not is_large_batch and selected_tickers:
        should_trigger = True
elif run_analysis:
    should_trigger = True
elif (tickers_changed or period_changed) and not is_large_batch:
    should_trigger = True

if "results" not in st.session_state and not should_trigger:
    st.info("💡 **Silakan pilih kategori saham di sidebar kiri dan klik '🔄 Jalankan & Simpan Analisis Baru'** untuk memulai screening.")

if should_trigger:
    st.session_state["last_selected_tickers"] = selected_tickers
    st.session_state["last_history_period"] = history_period
    
    with st.spinner("Menarik data terupdate & memproses indikator teknikal..."):
        all_results = []
        raw_histories = {}
        
        # Save to logs database/CSV
        storage.log_activity(st.session_state["username"], "RUN_SCREENER", f"{len(selected_tickers)} stocks")
        
        for ticker in selected_tickers:
            df_hist = loader.fetch_historical_data(ticker, period=history_period)
            if df_hist is None or df_hist.empty:
                st.warning(f"Gagal mengambil data historis untuk {ticker}. Mengabaikan ticker.")
                continue
                
            indicators = calculate_technical_indicators(df_hist)
            if indicators is None:
                st.warning(f"Data historis {ticker} tidak cukup untuk analisis (minimum 60 bar).")
                continue
                
            raw_histories[ticker] = indicators.pop("history")
            
            # Fetch latest live price details
            quote = loader.fetch_latest_quote(ticker)
            close_price = quote.get("currentPrice", indicators["close"])
            indicators["close"] = close_price
            
            # Fetch Bandarmologi Flow data from CSV
            df_broker = loader.fetch_broker_summary(ticker)
            df_foreign = loader.fetch_foreign_flow(ticker)
            
            # Scoring
            score_data = calculate_score(indicators, df_broker, df_foreign)
            
            # Create full record
            record = {
                "tanggal": date.today(),
                "ticker": ticker,
                "name": quote.get("name", IDX_STOCKS.get(ticker, ticker.split(".")[0])),
                "close_price": close_price,
                "open": quote.get("open", indicators["open"]),
                "high": quote.get("high", indicators["high"]),
                "low": quote.get("low", indicators["low"]),
                "volume": quote.get("volume", indicators["volume"]),
                "rsi": indicators["rsi"],
                "ma20": indicators["ma20"],
                "ma50": indicators["ma50"],
                "momentum_1m": indicators["momentum_1m"],
                "momentum_3m": indicators["momentum_3m"],
                "momentum_1m_pct": indicators["momentum_1m_pct"],
                "momentum_3m_pct": indicators["momentum_3m_pct"],
                "volume_ratio": indicators["volume_ratio"],
                
                # New metrics
                "technical_score": score_data["technical_score"],
                "flow_score": score_data["flow_score"],
                "score": score_data["final_score"], # final_score -> logged to DB as 'score'
                "recommendation": score_data["recommendation"], # Signal (BUY/HOLD/AVOID)
                "reasons": score_data["reasons"],
                "risks": score_data["risks"],
                "entry_area": score_data["entry_area"],
                "tp1": score_data["tp1"],
                "tp2": score_data["tp2"],
                "sl": score_data["sl"],
                "risk_reward_ratio": score_data["risk_reward_ratio"],
                "entry_reason": score_data["entry_reason"],
                
                # Support/Resistance indicators
                "support_20d": indicators["support_20d"],
                "resistance_20d": indicators["resistance_20d"],
                "support_50d": indicators["support_50d"],
                "resistance_50d": indicators["resistance_50d"],
                "high_20d": indicators["high_20d"],
                "low_20d": indicators["low_20d"],
                "distance_from_20d_low": indicators["distance_from_20d_low"],
                "distance_from_20d_high": indicators["distance_from_20d_high"],
                
                # Raw datasets for details
                "flow_data": score_data["flow_data"],
                "df_broker": df_broker,
                "df_foreign": df_foreign
            }
            all_results.append(record)
            
        if all_results:
            st.session_state["results"] = all_results
            st.session_state["histories"] = raw_histories
            
            # Sync to Database
            db_save_records = []
            for r in all_results:
                db_save_records.append({
                    "tanggal": r["tanggal"],
                    "ticker": r["ticker"],
                    "close_price": r["close_price"],
                    "rsi": r["rsi"],
                    "ma20": r["ma20"],
                    "ma50": r["ma50"],
                    "momentum_1m": r["momentum_1m"],
                    "momentum_3m": r["momentum_3m"],
                    "volume_ratio": r["volume_ratio"],
                    "score": r["score"], # final_score
                    "recommendation": r["recommendation"]
                })
            saved = storage.save_analysis(db_save_records)
            if saved:
                st.session_state["saved_status"] = "✅ Analisis berhasil disimpan ke Database!"
            else:
                st.session_state["saved_status"] = "⚠️ Analisis selesai tetapi gagal sinkronisasi database."
                
            # Auto-send BUY alerts to Telegram
            if auto_send_buy and tg_bot_token and tg_chat_id:
                sent_count = 0
                for r in all_results:
                    if r["recommendation"] == "BUY":
                        success, msg = send_telegram_alert(tg_bot_token, tg_chat_id, r)
                        if success:
                            sent_count += 1
                if sent_count > 0:
                    st.toast(f"🔔 Berhasil mengirim {sent_count} alert sinyal BUY ke Telegram!", icon="🚀")
        else:
            st.error("Tidak ada saham yang berhasil dianalisis. Harap pastikan format ticker benar (contoh: BBCA.JK atau BBCA).")

# ----------------- VIEW LAYER: RENDER DASHBOARD CONTENTS -----------------

if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]
    histories = st.session_state["histories"]
    
    if "saved_status" in st.session_state:
        st.caption(st.session_state["saved_status"])
        
    tab_screener, tab_history, tab_activities = st.tabs(["📊 Screener & Ranking", "📜 Histori Rekomendasi", "🔐 Audit Aktivitas User (Neon DB)"])
    
    with tab_screener:
        # Highlights Metrics Layout
        buy_count = sum(1 for r in results if r["recommendation"] == "BUY")
        watch_count = sum(1 for r in results if r["recommendation"] == "HOLD / WATCH")
        avoid_count = sum(1 for r in results if r["recommendation"] == "AVOID")
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #3b82f6;"><div class="metric-grid-lbl">Saham Di-Screen</div><div class="metric-grid-val" style="color:#3b82f6;">{len(results)}</div></div>', unsafe_allow_html=True)
        with col_m2:
            st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #10b981;"><div class="metric-grid-lbl">Sinyal BUY</div><div class="metric-grid-val" style="color:#10b981;">{buy_count}</div></div>', unsafe_allow_html=True)
        with col_m3:
            st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #f59e0b;"><div class="metric-grid-lbl">Sinyal HOLD / WATCH</div><div class="metric-grid-val" style="color:#f59e0b;">{watch_count}</div></div>', unsafe_allow_html=True)
        with col_m4:
            st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #ef4444;"><div class="metric-grid-lbl">Sinyal AVOID</div><div class="metric-grid-val" style="color:#ef4444;">{avoid_count}</div></div>', unsafe_allow_html=True)
            
        st.write("")
        col_tbl_title, col_tbl_filter = st.columns([2, 1])
        with col_tbl_title:
            st.subheader("🏆 Leaderboard Hasil Screening Saham")
        with col_tbl_filter:
            signal_filter = st.multiselect(
                "Filter Sinyal:",
                options=["BUY", "HOLD / WATCH", "AVOID"],
                default=["BUY", "HOLD / WATCH", "AVOID"]
            )
        
        table_data = []
        for r in results:
            fd = r["flow_data"]
            table_data.append({
                "Ticker": r["ticker"],
                "Last Price": f"Rp {r['close_price']:,.0f}",
                "RSI": f"{r['rsi']:.1f}" if r['rsi'] is not None else "N/A",
                "MA20": f"Rp {r['ma20']:,.0f}" if r['ma20'] is not None else "N/A",
                "MA50": f"Rp {r['ma50']:,.0f}" if r['ma50'] is not None else "N/A",
                "Momentum 1M": f"{r['momentum_1m_pct']:+.2f}%",
                "Momentum 3M": f"{r['momentum_3m_pct']:+.2f}%",
                "Volume Ratio": f"{r['volume_ratio']:.2f}x",
                "Technical Score": r["technical_score"],
                "Flow Score": r["flow_score"] if r["flow_score"] is not None else "N/A",
                "Final Score": r["score"],
                "Signal": r["recommendation"],
                "Entry Area": r["entry_area"],
                "TP1": f"Rp {r['tp1']:,}" if isinstance(r['tp1'], (int, float)) else r['tp1'],
                "TP2": f"Rp {r['tp2']:,}" if isinstance(r['tp2'], (int, float)) else r['tp2'],
                "SL": f"Rp {r['sl']:,}" if isinstance(r['sl'], (int, float)) else r['sl'],
                "Risk Reward": r["risk_reward_ratio"],
                "Main Reason": r["entry_reason"],
                "Risk Note": "; ".join([risk.replace("[Teknikal] ", "").replace("[Flow] ", "").replace("[Sinyal] ", "") for risk in r["risks"] if "Tidak ada" not in risk][:2]),
                "Data Status": fd["data_status"]
            })
            
        df_table = pd.DataFrame(table_data).sort_values(by="Final Score", ascending=False).reset_index(drop=True)
        
        # Apply dynamic signal filtering
        df_table_filtered = df_table[df_table['Signal'].isin(signal_filter)].reset_index(drop=True)
        
        def style_recommendation(val):
            if val == "BUY":
                return 'background-color: rgba(16, 185, 129, 0.25); color: #10b981; font-weight: bold; border: 1px solid #10b981;'
            elif val == "HOLD / WATCH":
                return 'background-color: rgba(245, 158, 11, 0.25); color: #f59e0b; font-weight: bold; border: 1px solid #f59e0b;'
            elif val == "AVOID":
                return 'background-color: rgba(239, 68, 68, 0.25); color: #ef4444; font-weight: bold; border: 1px solid #ef4444;'
            return ''
            
        styler = df_table_filtered.style
        if hasattr(styler, "map"):
            styled_df = styler.map(style_recommendation, subset=["Signal"])
        else:
            styled_df = styler.applymap(style_recommendation, subset=["Signal"])
            
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)
        
        # ----------------- SECTION: WOW KICK DETAILED ANALYSIS -----------------
        st.markdown("### 🔍 Analisis Komprehensif & Visualisasi Interaktif")
        
        # Align selectbox options with current signal filters
        filtered_detail_options = [r["ticker"] for r in results if r["recommendation"] in signal_filter]
        if not filtered_detail_options:
            filtered_detail_options = [r["ticker"] for r in results]
            
        selected_stock = st.selectbox(
            "Pilih Saham untuk Analisis Detil:",
            options=filtered_detail_options,
            format_func=lambda x: f"{x} - {IDX_STOCKS.get(x, 'Custom Ticker')}"
        )
        
        # User activity logging for stock view (triggered only once per unique stock click)
        if "last_viewed" not in st.session_state or st.session_state["last_viewed"] != selected_stock:
            st.session_state["last_viewed"] = selected_stock
            storage.log_activity(st.session_state["username"], "VIEW_STOCK_DETAILS", selected_stock)
            
        stock_details = next(r for r in results if r["ticker"] == selected_stock)
        stock_hist = histories[selected_stock]
        
        col_det_left, col_det_right = st.columns([5, 3])
        
        with col_det_left:
            st.markdown(f"##### Grafik Candlestick, MA, & Price Channels (20D Support/Resistance): **{selected_stock}**")
            
            # Chart period selector
            chart_range = st.radio("Rentang Tampilan:", ["3 Bulan", "6 Bulan", "1 Tahun"], horizontal=True, key="c_range")
            if chart_range == "3 Bulan":
                df_chart = stock_hist.tail(60).copy()
            elif chart_range == "6 Bulan":
                df_chart = stock_hist.tail(120).copy()
            else:
                df_chart = stock_hist.copy()
                
            fig = go.Figure()
            
            # Candlestick
            fig.add_trace(go.Candlestick(
                x=df_chart['Date'],
                open=df_chart['Open'],
                high=df_chart['High'],
                low=df_chart['Low'],
                close=df_chart['Close'],
                name="Harga Saham",
                increasing_line_color='#10b981',
                decreasing_line_color='#ef4444'
            ))
            
            # MA 20
            if 'MA20' in df_chart.columns:
                fig.add_trace(go.Scatter(
                    x=df_chart['Date'], y=df_chart['MA20'],
                    line=dict(color='#3b82f6', width=2),
                    name='MA 20'
                ))
            # MA 50
            if 'MA50' in df_chart.columns:
                fig.add_trace(go.Scatter(
                    x=df_chart['Date'], y=df_chart['MA50'],
                    line=dict(color='#f59e0b', width=2),
                    name='MA 50'
                ))
                
            # Support 20D (dotted red line)
            if 'Support20D' in df_chart.columns:
                fig.add_trace(go.Scatter(
                    x=df_chart['Date'], y=df_chart['Support20D'],
                    line=dict(color='#ef4444', width=1.5, dash='dash'),
                    name='Support 20D (Lowest Low)'
                ))
            # Resistance 20D (dotted green line)
            if 'Resistance20D' in df_chart.columns:
                fig.add_trace(go.Scatter(
                    x=df_chart['Date'], y=df_chart['Resistance20D'],
                    line=dict(color='#10b981', width=1.5, dash='dash'),
                    name='Resistance 20D (Highest High)'
                ))
                
            fig.update_layout(
                template="plotly_dark",
                xaxis_rangeslider_visible=False,
                margin=dict(l=20, r=20, t=10, b=10),
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Volume Chart with MA20 Volume line
            st.markdown(f"##### Volume Transaksi Harian & Rata-rata 20 Hari: **{selected_stock}**")
            fig_vol = go.Figure()
            fig_vol.add_trace(go.Bar(
                x=df_chart['Date'], y=df_chart['Volume'],
                marker_color='rgba(59, 130, 246, 0.4)',
                name='Volume Harian'
            ))
            fig_vol.add_trace(go.Scatter(
                x=df_chart['Date'], y=df_chart['Vol_MA20'],
                line=dict(color='#3b82f6', width=2),
                name='Vol MA20'
            ))
            fig_vol.update_layout(
                template="plotly_dark",
                margin=dict(l=20, r=20, t=10, b=10),
                height=180,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_vol, use_container_width=True)
            
            # RSI Chart
            st.markdown(f"##### Indikator Relative Strength Index (RSI 14): **{selected_stock}**")
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(
                x=df_chart['Date'], y=df_chart['RSI'],
                line=dict(color='#a78bfa', width=2),
                fill='tozeroy',
                fillcolor='rgba(167, 139, 250, 0.05)',
                name='RSI 14'
            ))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="#ef4444", annotation_text="Overbought (70)")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="#10b981", annotation_text="Oversold (30)")
            fig_rsi.add_hline(y=40, line_dash="dot", line_color="#94a3b8", annotation_text="Neutral Low (40)")
            
            fig_rsi.update_layout(
                template="plotly_dark",
                yaxis=dict(range=[10, 90]),
                margin=dict(l=20, r=20, t=10, b=10),
                height=180,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_rsi, use_container_width=True)
            
        with col_det_right:
            # WOW KICK GAUGE CHART
            st.markdown("<div class='glass-card' style='text-align:center;'>", unsafe_allow_html=True)
            
            score = stock_details["score"]
            rec = stock_details["recommendation"]
            
            # Gauge Plotly Chart
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#ffffff"},
                    'bar': {'color': "#ffffff", 'thickness': 0.25},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': "rgba(255,255,255,0.1)",
                    'steps': [
                        {'range': [0, 55], 'color': '#ef4444'},
                        {'range': [55, 75], 'color': '#f59e0b'},
                        {'range': [75, 100], 'color': '#10b981'}
                    ],
                    'threshold': {
                        'line': {'color': "#ffffff", 'width': 4},
                        'thickness': 0.75,
                        'value': score
                    }
                }
            ))
            fig_gauge.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "#ffffff", 'family': "Arial"},
                height=220,
                margin=dict(l=30, r=30, t=30, b=10)
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            rec_badge_style = "badge-buy" if rec == "BUY" else ("badge-watch" if rec == "HOLD / WATCH" else "badge-avoid")
            st.markdown(f"""
            <div style="margin-top:-20px; margin-bottom:15px;">
                <span class="badge {rec_badge_style}" style="font-size:1.4rem; padding:8px 25px; border-radius:30px;">
                    {rec}
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            # Manual Telegram push button
            if tg_bot_token and tg_chat_id:
                if st.button("📤 Kirim Sinyal Ke Telegram", key="btn_send_tg", use_container_width=True):
                    with st.spinner("Mengirim alert telegram..."):
                        success, msg = send_telegram_alert(tg_bot_token, tg_chat_id, stock_details)
                        if success:
                            st.toast("✅ Sinyal dikirim ke Telegram!", icon="🔔")
                            st.success(msg)
                        else:
                            st.error(msg)
                            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Combined Grid Score Dashboard
            st.markdown("##### 🔢 Detail Bobot Penilaian")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Skor Teknikal (60%)</div><div class="metric-grid-val" style="color:#60a5fa;">{stock_details["technical_score"]}</div></div>', unsafe_allow_html=True)
            with col_t2:
                flow_s_val = f"{stock_details['flow_score']}" if stock_details['flow_score'] is not None else "N/A"
                st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Skor Flow (40%)</div><div class="metric-grid-val" style="color:#a78bfa;">{flow_s_val}</div></div>', unsafe_allow_html=True)
                
            st.write("")
            
            # --- TRADING SIGNAL SETUP SECTION ---
            st.markdown("##### 🎯 Rekomendasi Sinyal Trading & Risk Setup")
            st.markdown(f"**Entry Area:** <span style='font-size:1.15rem; color:#60a5fa; font-weight:700;'>{stock_details['entry_area']}</span>", unsafe_allow_html=True)
            
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                tp1_val = f"Rp {stock_details['tp1']:,}" if isinstance(stock_details['tp1'], (int, float)) else stock_details['tp1']
                st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">TP 1</div><div class="metric-grid-val" style="color:#34d399; font-size:1.1rem; padding-top:4px;">{tp1_val}</div></div>', unsafe_allow_html=True)
            with col_s2:
                tp2_val = f"Rp {stock_details['tp2']:,}" if isinstance(stock_details['tp2'], (int, float)) else stock_details['tp2']
                st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">TP 2</div><div class="metric-grid-val" style="color:#10b981; font-size:1.1rem; padding-top:4px;">{tp2_val}</div></div>', unsafe_allow_html=True)
            with col_s3:
                sl_val = f"Rp {stock_details['sl']:,}" if isinstance(stock_details['sl'], (int, float)) else stock_details['sl']
                st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Stop Loss</div><div class="metric-grid-val" style="color:#f87171; font-size:1.1rem; padding-top:4px;">{sl_val}</div></div>', unsafe_allow_html=True)
            with col_s4:
                st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">R/R Ratio</div><div class="metric-grid-val" style="font-size:1.1rem; padding-top:4px;">{stock_details["risk_reward_ratio"]}</div></div>', unsafe_allow_html=True)
            
            st.write("")
            st.markdown(f"💡 **Alasan Setup:** {stock_details['entry_reason']}")
            
            # Bandarmologi summary section
            st.markdown("##### 🐳 Hasil Analisis Bandarmologi & Flow")
            fd = stock_details["flow_data"]
            if stock_details["flow_score"] is None:
                st.warning("⚠️ Data bandarmologi tidak tersedia.")
            else:
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1:
                    f_net_1d = fd["foreign_net_1d"]
                    f_color = "#10b981" if f_net_1d > 0 else "#ef4444"
                    st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Foreign 1D</div><div class="metric-grid-val" style="color:{f_color}; font-size:1.0rem;">Rp {f_net_1d/1e9:+.1f}B</div></div>', unsafe_allow_html=True)
                with col_f2:
                    f_net_5d = fd["foreign_net_5d"]
                    f_color = "#10b981" if f_net_5d > 0 else "#ef4444"
                    st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Foreign 5D</div><div class="metric-grid-val" style="color:{f_color}; font-size:1.0rem;">Rp {f_net_5d/1e9:+.1f}B</div></div>', unsafe_allow_html=True)
                with col_f3:
                    f_net_20d = fd["foreign_net_20d"]
                    f_color = "#10b981" if f_net_20d > 0 else "#ef4444"
                    st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Foreign 20D</div><div class="metric-grid-val" style="color:{f_color}; font-size:1.0rem;">Rp {f_net_20d/1e9:+.1f}B</div></div>', unsafe_allow_html=True)
                    
                st.write("")
                st.markdown(f"**Top Buyer Brokers:** {fd['top_buyer_brokers']} (Accumulation: `{fd['broker_accumulation_signal']}`)")
                st.markdown(f"**Top Seller Brokers:** {fd['top_seller_brokers']} (Distribution: `{fd['broker_distribution_signal']}`)")
                
                # Render top 5 buyers/sellers summaries
                df_b = stock_details["df_broker"]
                if df_b is not None and not df_b.empty:
                    with st.expander("🔍 Detail Top 5 Transaksi Broker Hari Ini"):
                        latest_date = df_b['date'].max()
                        df_b_latest = df_b[df_b['date'] == latest_date].copy()
                        broker_summary = df_b_latest.groupby(['broker_code', 'broker_name']).agg({'net_value': 'sum'}).reset_index()
                        
                        df_buyers = broker_summary[broker_summary['net_value'] > 0].sort_values('net_value', ascending=False).head(5)
                        df_sellers = broker_summary[broker_summary['net_value'] < 0].sort_values('net_value', ascending=True).head(5)
                        
                        df_buyers_disp = pd.DataFrame({
                            "Kode": df_buyers["broker_code"],
                            "Broker Buyer": df_buyers["broker_name"],
                            "Net Buy (Rp)": df_buyers["net_value"].apply(lambda x: f"Rp {x:,.0f}")
                        }).reset_index(drop=True)
                        
                        df_sellers_disp = pd.DataFrame({
                            "Kode": df_sellers["broker_code"],
                            "Broker Seller": df_sellers["broker_name"],
                            "Net Sell (Rp)": df_sellers["net_value"].abs().apply(lambda x: f"Rp {x:,.0f}")
                        }).reset_index(drop=True)
                        
                        col_br_b, col_br_s = st.columns(2)
                        with col_br_b:
                            st.caption("Top 5 Buyers")
                            st.dataframe(df_buyers_disp, hide_index=True)
                        with col_br_s:
                            st.caption("Top 5 Sellers")
                            st.dataframe(df_sellers_disp, hide_index=True)

            # Display reasons & risks lists
            with st.expander("🟢 Rincian Analisis (Teknikal & Flow)", expanded=False):
                for reason in stock_details["reasons"]:
                    st.markdown(f"**✓** {reason}")
                    
            with st.expander("⚠️ Faktor Risiko Singkat Terdeteksi", expanded=True):
                for risk in stock_details["risks"]:
                    # Color code systems messages
                    risk_color = "#f87171" if "[Sistem]" not in risk else "#60a5fa"
                    st.markdown(f"**•** <span style='color:{risk_color}'>{risk}</span>", unsafe_allow_html=True)
                    
    with tab_history:
        st.subheader("📜 Log Riwayat Analisis Harian")
        st.write("Histori data screening harian yang tercatat di database online Neon DB / database SQLite lokal.")
        
        try:
            df_logs = storage.load_historical_logs(limit=250)
            if not df_logs.empty:
                df_logs['tanggal'] = pd.to_datetime(df_logs['tanggal']).dt.date
                df_logs = df_logs.rename(columns={
                    'tanggal': 'Tanggal', 'ticker': 'Ticker', 'close_price': 'Harga Close',
                    'rsi': 'RSI', 'ma20': 'MA 20', 'ma50': 'MA 50', 'momentum_1m': 'Momentum 1M',
                    'momentum_3m': 'Momentum 3M', 'volume_ratio': 'Vol Ratio', 'score': 'Skor',
                    'recommendation': 'Rekomendasi'
                })
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.info("Log database masih kosong. Jalankan screening baru di sidebar untuk mengisi database.")
        except Exception as e:
            st.error(f"Gagal memuat log data dari database: {str(e)}")
            
    with tab_activities:
        st.subheader("🔐 Audit Jejak Aktivitas Pengguna (Neon DB Sync)")
        st.write("Semua aktivitas pengguna seperti masuk akun, melihat grafik saham spesifik, dan melakukan screening tersimpan di Neon DB untuk monitoring.")
        
        try:
            df_act = storage.load_activity_logs(limit=150)
            if not df_act.empty:
                df_act['timestamp'] = pd.to_datetime(df_act['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                df_act = df_act.rename(columns={
                    'username': 'Username',
                    'action': 'Aktivitas / Tindakan',
                    'ticker': 'Ticker Terkait',
                    'timestamp': 'Waktu (UTC)'
                })
                st.dataframe(df_act, use_container_width=True, hide_index=True)
            else:
                st.info("Log aktivitas masih kosong.")
        except Exception as e:
            st.error(f"Gagal mengambil log aktivitas pengguna: {str(e)}")

# Bottom Disclaimer Page Footer
st.markdown('<div class="header-divider" style="margin-top:40px;"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="background-color: rgba(39, 39, 42, 0.4); border-radius: 12px; padding: 20px; border-left: 6px solid #f59e0b; margin-top: 10px;">
    <h5 style="color: #f59e0b; margin: 0 0 5px 0; font-weight:700;">⚠️ DISCLAIMER & BATASAN PENGGUNAAN</h5>
    <p style="color: #cbd5e1; font-size: 0.85rem; margin: 0; line-height:1.4;">
        <b>Hasil ini hanya untuk alat bantu analisis awal, bukan rekomendasi investasi final atau ajakan membeli/menjual saham.</b> 
        Setiap keputusan transaksi saham sepenuhnya menjadi tanggung jawab mandiri pengguna. Anda sangat disarankan untuk menyelaraskan hasil screening ini dengan 
        analisis fundamental perusahaan, broker summary, serta memantau berita pasar modal secara menyeluruh sebelum melakukan jual-beli saham.
    </p>
</div>
""", unsafe_allow_html=True)
st.write("")
