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

# Set page configuration with a modern title and wide layout
st.set_page_config(
    page_title="Smart Saham - ID Stock Screener & Recommendation Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics and modern card styling
st.markdown("""
<style>
    /* Main body background styling */
    .reportview-container {
        background-color: #0e1117;
    }
    /* Premium card containers */
    .metric-card {
        background-color: #1e222b;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #2d3139;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 5px 0;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #8a99ad;
        font-weight: 500;
        text-transform: uppercase;
    }
    /* Recommendation badges */
    .badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85rem;
        text-align: center;
        display: inline-block;
    }
    .badge-buy {
        background-color: #10b981;
        color: white;
    }
    .badge-watch {
        background-color: #f59e0b;
        color: #1e1b4b;
    }
    .badge-avoid {
        background-color: #ef4444;
        color: white;
    }
    /* Custom divider line */
    .divider {
        height: 2px;
        background: linear-gradient(90deg, #3b82f6 0%, #10b981 100%);
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize modules
@st.cache_resource
def get_loader():
    return StockDataLoader()

# Database URL support from st.secrets (Streamlit Cloud) or environment variable
db_url = None
try:
    if "DATABASE_URL" in st.secrets:
        db_url = st.secrets["DATABASE_URL"]
except Exception:
    # st.secrets is not set up or configured (common in local environment)
    pass

if not db_url:
    db_url = os.environ.get("DATABASE_URL")

storage = AnalysisStorage(db_url=db_url)
loader = get_loader()

# Default stock tickers
DEFAULT_TICKERS = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK",
    "UNVR.JK", "ICBP.JK", "GOTO.JK", "ADRO.JK", "MDKA.JK"
]

# Title banner
st.title("📈 Smart Saham - Prototype Rekomendasi Saham Indonesia")
st.markdown("##### *Decision-Support Tool untuk Analisis Awal Saham IDX (Near-Live Data via yfinance)*")
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# Sidebar configurations
with st.sidebar:
    st.header("⚙️ Pengaturan Analisis")
    
    # Custom ticker input list
    selected_tickers = st.multiselect(
        "Pilih Saham untuk Dianalisis",
        options=DEFAULT_TICKERS,
        default=DEFAULT_TICKERS,
        help="Anda dapat menghapus atau memilih daftar saham Indonesia berformat .JK"
    )
    
    # Additional ticker input
    custom_ticker = st.text_input("Tambah Ticker Custom (Contoh: BBNI.JK)", "")
    if custom_ticker:
        ticker_to_add = custom_ticker.strip().upper()
        if not ticker_to_add.endswith(".JK"):
            ticker_to_add += ".JK"
        if ticker_to_add not in selected_tickers:
            selected_tickers.append(ticker_to_add)
            
    # Period of analysis
    history_period = st.selectbox(
        "Rentang Data Historis",
        options=["6mo", "1y", "2y"],
        index=1,
        help="yfinance akan mengambil data sepanjang masa waktu ini untuk menghitung rata-rata bergerak (MA)."
    )
    
    st.markdown("---")
    # Neon DB Connection Info
    st.subheader("🌐 Cloud Database Sync")
    if db_url:
        st.success("Terkoneksi ke Neon DB Cloud PostgreSQL")
    else:
        st.info("Menggunakan Database Lokal (SQLite/CSV)")
        st.caption("Untuk sinkronisasi cloud, tambahkan rahasia `DATABASE_URL` di Streamlit secrets atau environment variable.")

    # Refresh button
    run_analysis = st.button("🔄 Jalankan & Simpan Analisis Baru", use_container_width=True)

# Application logic & states
if "results" not in st.session_state or run_analysis:
    with st.spinner("Mengambil data saham terkini dari yfinance..."):
        all_results = []
        raw_histories = {}
        quotes = {}
        
        for ticker in selected_tickers:
            # 1. Fetch History
            df_hist = loader.fetch_historical_data(ticker, period=history_period)
            if df_hist is None or df_hist.empty:
                st.warning(f"Gagal mengambil data historis untuk ticker {ticker}. Mengabaikan ticker.")
                continue
                
            # 2. Calculate Indicators
            indicators = calculate_technical_indicators(df_hist)
            if indicators is None:
                st.warning(f"Data historis ticker {ticker} terlalu sedikit (kurang dari 60 hari perdagangan).")
                continue
                
            # Store history for visualization
            raw_histories[ticker] = indicators.pop("history") # Extract history df to avoid cluttering indicators dict
            
            # 3. Fetch Quote for live price
            quote = loader.fetch_latest_quote(ticker)
            quotes[ticker] = quote
            
            # Use live price if available, otherwise fallback to historical last close
            close_price = quote.get("currentPrice", indicators["close"])
            indicators["close"] = close_price
            
            # 4. Calculate Score
            score_data = calculate_score(indicators)
            
            # Combine record
            record = {
                "tanggal": date.today(),
                "ticker": ticker,
                "name": quote.get("name", ticker.split(".")[0]),
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
            
            # Auto save to Database & CSV
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
                st.session_state["saved_status"] = "✅ Hasil analisis berhasil disimpan ke Database & CSV!"
            else:
                st.session_state["saved_status"] = "⚠️ Analisis selesai tetapi gagal disimpan ke database."
        else:
            st.error("Gagal mendapatkan data untuk semua ticker yang dipilih. Silakan periksa jaringan internet atau nama ticker.")

# Display main contents if results are in session state
if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]
    histories = st.session_state["histories"]
    
    # Save status banner
    if "saved_status" in st.session_state:
        st.caption(st.session_state["saved_status"])
        
    # Tab navigation
    tab_dashboard, tab_historical_logs = st.tabs(["📊 Dashboard Utama & Screener", "📜 Riwayat Log Analisis"])
    
    with tab_dashboard:
        # Counters and Highlights
        total_stocks = len(results)
        buy_count = sum(1 for r in results if r["recommendation"] == "BUY")
        watch_count = sum(1 for r in results if r["recommendation"] == "WATCH")
        avoid_count = sum(1 for r in results if r["recommendation"] == "AVOID")
        
        # Metric Cards Layout
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 5px solid #3b82f6;">
                <div class="metric-label">Total Saham</div>
                <div class="metric-value" style="color: #3b82f6;">{total_stocks}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 5px solid #10b981;">
                <div class="metric-label">Rekomendasi BUY</div>
                <div class="metric-value" style="color: #10b981;">{buy_count}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 5px solid #f59e0b;">
                <div class="metric-label">Rekomendasi WATCH</div>
                <div class="metric-value" style="color: #f59e0b;">{watch_count}</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 5px solid #ef4444;">
                <div class="metric-label">Rekomendasi AVOID</div>
                <div class="metric-value" style="color: #ef4444;">{avoid_count}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("")
        st.subheader("🏆 Tabel Ranking Saham Terkini (Urutan Berdasarkan Skor Tertinggi)")
        
        # Convert results to DataFrame for rendering
        table_data = []
        for r in results:
            table_data.append({
                "Ticker": r["ticker"],
                "Nama Perusahaan": r["name"],
                "Harga Terakhir": f"Rp {r['close_price']:,.0f}",
                "RSI (14)": f"{r['rsi']:.1f}" if r['rsi'] is not None else "N/A",
                "MA 20": f"Rp {r['ma20']:,.0f}" if r['ma20'] is not None else "N/A",
                "MA 50": f"Rp {r['ma50']:,.0f}" if r['ma50'] is not None else "N/A",
                "Momentum 1M": f"{r['momentum_1m_pct']:+.2f}%",
                "Momentum 3M": f"{r['momentum_3m_pct']:+.2f}%",
                "Volume Ratio": f"{r['volume_ratio']:.2f}x",
                "Skor (0-100)": r["score"],
                "Rekomendasi": r["recommendation"]
            })
        
        df_table = pd.DataFrame(table_data)
        # Sort by score descending
        df_table = df_table.sort_values(by="Skor (0-100)", ascending=False).reset_index(drop=True)
        
        # Highlight Recommendations with streamlit coloring API
        def style_recommendation(val):
            if val == "BUY":
                return 'background-color: #10b981; color: white; font-weight: bold;'
            elif val == "WATCH":
                return 'background-color: #f59e0b; color: black; font-weight: bold;'
            elif val == "AVOID":
                return 'background-color: #ef4444; color: white; font-weight: bold;'
            return ''

        st.dataframe(
            df_table.style.applymap(style_recommendation, subset=["Rekomendasi"]),
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("---")
        
        # Section detail per saham
        st.subheader("🔍 Analisis Detail & Grafik per Saham")
        selected_stock = st.selectbox(
            "Pilih Saham untuk Melihat Grafik & Detail Alasan:",
            options=[r["ticker"] for r in results]
        )
        
        # Find stock result details
        stock_details = next(r for r in results if r["ticker"] == selected_stock)
        stock_hist = histories[selected_stock]
        
        col_detail_left, col_detail_right = st.columns([2, 1])
        
        with col_detail_left:
            st.markdown(f"#### Grafik Harga Historis: **{selected_stock}**")
            
            # Filter chart view options
            chart_period = st.radio("Jangka Waktu Tampilan Grafik:", ["3 Bulan", "6 Bulan", "Semua Data"], horizontal=True, key="chart_p")
            if chart_period == "3 Bulan":
                df_chart = stock_hist.tail(60).copy()
            elif chart_period == "6 Bulan":
                df_chart = stock_hist.tail(120).copy()
            else:
                df_chart = stock_hist.copy()
            
            # Interactive Candlestick / Line Chart using Plotly
            fig = go.Figure()
            
            # Price Candlestick
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
                    line=dict(color='#3b82f6', width=1.5),
                    name='MA 20 (Tren Jk. Pendek)'
                ))
                
            # MA 50
            if 'MA50' in df_chart.columns:
                fig.add_trace(go.Scatter(
                    x=df_chart['Date'], y=df_chart['MA50'],
                    line=dict(color='#f59e0b', width=1.5),
                    name='MA 50 (Tren Jk. Menengah)'
                ))
                
            fig.update_layout(
                template="plotly_dark",
                xaxis_rangeslider_visible=False,
                margin=dict(l=20, r=20, t=10, b=10),
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # RSI Chart
            st.markdown(f"#### Grafik Relative Strength Index (RSI 14): **{selected_stock}**")
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(
                x=df_chart['Date'], y=df_chart['RSI'],
                line=dict(color='#8b5cf6', width=2),
                name='RSI'
            ))
            # Boundaries
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="#ef4444", annotation_text="Overbought (70)")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="#10b981", annotation_text="Oversold (30)")
            fig_rsi.add_hline(y=40, line_dash="dot", line_color="#8a99ad", annotation_text="Batas Bawah Netral (40)")
            
            fig_rsi.update_layout(
                template="plotly_dark",
                yaxis=dict(range=[10, 90]),
                margin=dict(l=20, r=20, t=10, b=10),
                height=200,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_rsi, use_container_width=True)
            
        with col_detail_right:
            # Score Gauge
            st.markdown("#### Detail Hasil Analisis")
            
            rec = stock_details["recommendation"]
            rec_color = "#10b981" if rec == "BUY" else ("#f59e0b" if rec == "WATCH" else "#ef4444")
            
            st.markdown(f"""
            <div style="background-color: #1e222b; border-radius: 12px; padding: 25px; border: 1px solid #2d3139; text-align: center;">
                <h5 style="color: #8a99ad; margin: 0;">SKOR REKOMENDASI</h5>
                <h1 style="color: {rec_color}; font-size: 4rem; margin: 5px 0;">{stock_details['score']}</h1>
                <div class="badge badge-{'buy' if rec == 'BUY' else ('watch' if rec == 'WATCH' else 'avoid')}" style="font-size: 1.2rem; padding: 8px 20px;">
                    {rec}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            
            # Display positive points
            st.markdown("##### 🟢 Poin Penilaian Positif:")
            if stock_details["reasons"]:
                for r in stock_details["reasons"]:
                    st.markdown(f"- {r}")
            else:
                st.caption("Tidak ada indikator teknikal positif signifikan terdeteksi.")
                
            st.write("")
            
            # Display risks
            st.markdown("##### ⚠️ Faktor Risiko Teknis & Catatan:")
            for risk in stock_details["risks"]:
                st.markdown(f"- <span style='color:#f87171'>{risk}</span>", unsafe_allow_html=True)
                
            # Basic stats summary card
            st.markdown("---")
            st.markdown("##### 📊 Statistik Harga Ringkas:")
            st.write(f"**Open Price:** Rp {stock_details['open']:,.0f}")
            st.write(f"**High Price:** Rp {stock_details['high']:,.0f}")
            st.write(f"**Low Price:** Rp {stock_details['low']:,.0f}")
            st.write(f"**Volume Harian:** {stock_details['volume']:,} lembar")
            
    with tab_historical_logs:
        st.subheader("📜 Log Riwayat Analisis Harian")
        st.write("Bagian ini menampilkan hasil analisis harian yang disimpan secara permanen di database (Neon DB/SQLite) maupun CSV lokal.")
        
        try:
            df_logs = storage.load_historical_logs(limit=200)
            if not df_logs.empty:
                # Format dates and numbers nicely
                df_logs['tanggal'] = pd.to_datetime(df_logs['tanggal']).dt.date
                df_logs = df_logs.rename(columns={
                    'tanggal': 'Tanggal',
                    'ticker': 'Ticker',
                    'close_price': 'Harga Close',
                    'rsi': 'RSI',
                    'ma20': 'MA 20',
                    'ma50': 'MA 50',
                    'momentum_1m': 'Momentum 1M',
                    'momentum_3m': 'Momentum 3M',
                    'volume_ratio': 'Vol Ratio',
                    'score': 'Skor',
                    'recommendation': 'Rekomendasi'
                })
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.info("Log database masih kosong. Silakan jalankan analisis saham baru di bilah samping kiri untuk menyimpannya.")
        except Exception as e:
            st.error(f"Gagal mengambil log dari database: {str(e)}")

# Disclaimer
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="background-color: #27272a; border-radius: 8px; padding: 15px; border-left: 6px solid #f59e0b; margin-top: 20px;">
    <h5 style="color: #f59e0b; margin: 0 0 5px 0;">⚠️ PENGUMUMAN PENTING & DISCLAIMER</h5>
    <p style="color: #d4d4d8; font-size: 0.85rem; margin: 0;">
        Hasil analisis dan rekomendasi (BUY / WATCH / AVOID) yang disajikan oleh dashboard Smart Saham ini murni berasal dari kalkulasi formula scoring indikator teknikal sederhana. 
        <b>Hasil ini hanya untuk analisis awal, bukan ajakan membeli/menjual saham.</b> Dashboard ini dirancang sebagai decision-support tool untuk menyaring saham (initial screening) 
        dan bukan merupakan financial advice final. Segala tindakan transaksi saham sepenuhnya menjadi tanggung jawab pengguna. Pengguna disarankan untuk melakukan analisis fundamental lebih lanjut, 
        serta memantau kondisi berita ekonomi sebelum mengambil keputusan investasi.
    </p>
</div>
""", unsafe_allow_html=True)
st.write("")
