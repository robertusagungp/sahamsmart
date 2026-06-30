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

@st.cache_resource
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
        # Extract sector name from preset
        sector_name = selected_preset.replace("Sektor ", "")
        if " (" in sector_name:
            sector_name = sector_name.split(" (")[0]
        
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

    run_analysis = st.button("🔄 Jalankan & Simpan Analisis Baru", use_container_width=True)

# ----------------- CONTROLLER / STOCK PROCESSING PIPELINE -----------------

if "results" not in st.session_state or run_analysis:
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
            
            # Scoring
            score_data = calculate_score(indicators)
            
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
                "score": score_data["score"],
                "recommendation": score_data["recommendation"],
                "reasons": score_data["reasons"],
                "risks": score_data["risks"]
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
                    "score": r["score"],
                    "recommendation": r["recommendation"]
                })
            saved = storage.save_analysis(db_save_records)
            if saved:
                st.session_state["saved_status"] = "✅ Analisis berhasil disimpan ke Database!"
            else:
                st.session_state["saved_status"] = "⚠️ Analisis selesai tetapi gagal sinkronisasi database."
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
        watch_count = sum(1 for r in results if r["recommendation"] == "WATCH")
        avoid_count = sum(1 for r in results if r["recommendation"] == "AVOID")
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #3b82f6;"><div class="metric-grid-lbl">Saham Di-Screen</div><div class="metric-grid-val" style="color:#3b82f6;">{len(results)}</div></div>', unsafe_allow_html=True)
        with col_m2:
            st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #10b981;"><div class="metric-grid-lbl">Rekomendasi BUY</div><div class="metric-grid-val" style="color:#10b981;">{buy_count}</div></div>', unsafe_allow_html=True)
        with col_m3:
            st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #f59e0b;"><div class="metric-grid-lbl">Rekomendasi WATCH</div><div class="metric-grid-val" style="color:#f59e0b;">{watch_count}</div></div>', unsafe_allow_html=True)
        with col_m4:
            st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #ef4444;"><div class="metric-grid-lbl">Rekomendasi AVOID</div><div class="metric-grid-val" style="color:#ef4444;">{avoid_count}</div></div>', unsafe_allow_html=True)
            
        st.write("")
        st.subheader("🏆 Leaderboard Hasil Screening Saham (Urutan Skor Tertinggi)")
        
        table_data = []
        for r in results:
            table_data.append({
                "Ticker": r["ticker"],
                "Nama Perusahaan": r["name"],
                "Harga Close": f"Rp {r['close_price']:,.0f}",
                "RSI 14": f"{r['rsi']:.1f}" if r['rsi'] is not None else "N/A",
                "MA 20": f"Rp {r['ma20']:,.0f}" if r['ma20'] is not None else "N/A",
                "MA 50": f"Rp {r['ma50']:,.0f}" if r['ma50'] is not None else "N/A",
                "Momentum 1M": f"{r['momentum_1m_pct']:+.2f}%",
                "Momentum 3M": f"{r['momentum_3m_pct']:+.2f}%",
                "Vol Ratio": f"{r['volume_ratio']:.2f}x",
                "Skor": r["score"],
                "Rekomendasi": r["recommendation"]
            })
            
        df_table = pd.DataFrame(table_data).sort_values(by="Skor", ascending=False).reset_index(drop=True)
        
        def style_recommendation(val):
            if val == "BUY":
                return 'background-color: rgba(16, 185, 129, 0.25); color: #10b981; font-weight: bold; border: 1px solid #10b981;'
            elif val == "WATCH":
                return 'background-color: rgba(245, 158, 11, 0.25); color: #f59e0b; font-weight: bold; border: 1px solid #f59e0b;'
            elif val == "AVOID":
                return 'background-color: rgba(239, 68, 68, 0.25); color: #ef4444; font-weight: bold; border: 1px solid #ef4444;'
            return ''
            
        styler = df_table.style
        if hasattr(styler, "map"):
            styled_df = styler.map(style_recommendation, subset=["Rekomendasi"])
        else:
            styled_df = styler.applymap(style_recommendation, subset=["Rekomendasi"])
            
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)
        
        # ----------------- SECTION: WOW KICK DETAILED ANALYSIS -----------------
        st.markdown("### 🔍 Analisis Komprehensif & Visualisasi Interaktif")
        
        selected_stock = st.selectbox(
            "Pilih Saham untuk Analisis Detil:",
            options=[r["ticker"] for r in results],
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
            st.markdown(f"##### Grafik Tren Candlestick & Moving Average: **{selected_stock}**")
            
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
                    name='MA 20 (Tren Pendek)'
                ))
            # MA 50
            if 'MA50' in df_chart.columns:
                fig.add_trace(go.Scatter(
                    x=df_chart['Date'], y=df_chart['MA50'],
                    line=dict(color='#f59e0b', width=2),
                    name='MA 50 (Tren Menengah)'
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
            
            # RSI Chart
            st.markdown(f"##### Indikator Kekuatan Harga (RSI 14): **{selected_stock}**")
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
                        {'range': [0, 50], 'color': '#ef4444'},
                        {'range': [50, 75], 'color': '#f59e0b'},
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
            
            rec_badge_style = "badge-buy" if rec == "BUY" else ("badge-watch" if rec == "WATCH" else "badge-avoid")
            st.markdown(f"""
            <div style="margin-top:-20px; margin-bottom:15px;">
                <span class="badge {rec_badge_style}" style="font-size:1.4rem; padding:8px 25px; border-radius:30px;">
                    {rec}
                </span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Technical Metrics Summary Grid
            st.markdown("##### 📝 Metrik Teknikal Utama")
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Harga Terakhir</div><div class="metric-grid-val">Rp {stock_details["close_price"]:,.0f}</div></div>', unsafe_allow_html=True)
                st.write("")
                st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">RSI (14)</div><div class="metric-grid-val">{stock_details["rsi"]:.1f}</div></div>', unsafe_allow_html=True)
                st.write("")
                st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Rasio Volume</div><div class="metric-grid-val">{stock_details["volume_ratio"]:.2f}x</div></div>', unsafe_allow_html=True)
            with col_g2:
                st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Momentum 1M</div><div class="metric-grid-val" style="color:{"#10b981" if stock_details["momentum_1m"] > 0 else "#ef4444"}">{stock_details["momentum_1m_pct"]:+.2f}%</div></div>', unsafe_allow_html=True)
                st.write("")
                st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Momentum 3M</div><div class="metric-grid-val" style="color:{"#10b981" if stock_details["momentum_3m"] > 0 else "#ef4444"}">{stock_details["momentum_3m_pct"]:+.2f}%</div></div>', unsafe_allow_html=True)
                st.write("")
                st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">MA20 vs MA50</div><div class="metric-grid-val" style="font-size:1.1rem; padding-top:4px;">{"MA20 > MA50" if (stock_details["ma20"] or 0) > (stock_details["ma50"] or 0) else "MA20 < MA50"}</div></div>', unsafe_allow_html=True)
                
            st.write("")
            
            # Bullet point reasons & risks
            with st.expander("🟢 Detail Poin Penilaian Positif", expanded=True):
                if stock_details["reasons"]:
                    for reason in stock_details["reasons"]:
                        st.markdown(f"**✓** {reason}")
                else:
                    st.caption("Tidak ada indikator teknikal positif terdeteksi saat ini.")
                    
            with st.expander("⚠️ Detail Faktor Risiko Teknis", expanded=True):
                if stock_details["risks"]:
                    for risk in stock_details["risks"]:
                        st.markdown(f"**•** <span style='color:#f87171'>{risk}</span>", unsafe_allow_html=True)
                else:
                    st.caption("Tidak ada faktor risiko teknis signifikan yang terdeteksi.")
                    
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
        Aplikasi Smart Saham Premium ini dirancang murni sebagai alat bantu pengambilan keputusan awal (decision-support tool) untuk mempermudah screening teknikal. 
        <b>Hasil analisis, nilai skor, dan rekomendasi (BUY / WATCH / AVOID) bukanlah saran keuangan final atau ajakan mutlak untuk membeli/menjual saham.</b> 
        Setiap keputusan transaksi saham sepenuhnya menjadi tanggung jawab mandiri pengguna. Anda sangat disarankan untuk menyelaraskan hasil screening ini dengan 
        analisis fundamental perusahaan serta memantau berita pasar modal secara menyeluruh.
    </p>
</div>
""", unsafe_allow_html=True)
st.write("")
