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
from src.stock_list import get_all_idx_tickers, get_idx_stocks_df, IDX_JII70_TICKERS, is_sharia_compliant
from src.telegram_bot import send_telegram_alert, send_telegram_photo
from src.portfolio_evaluator import run_portfolio_evaluation
from src.share_card import generate_share_card

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

    /* Landing Page Hero CSS */
    .hero-container {
        text-align: center;
        padding: 60px 20px 30px 20px;
        background: radial-gradient(circle at 50% 50%, rgba(59, 130, 246, 0.08) 0%, rgba(0, 0, 0, 0) 70%);
        border-radius: 20px;
        margin-bottom: 20px;
    }
    .hero-headline {
        font-size: 3.2rem;
        font-weight: 800;
        line-height: 1.25;
        background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    .hero-subheadline {
        font-size: 1.25rem;
        color: #94a3b8;
        max-width: 850px;
        margin: 0 auto 30px auto;
        line-height: 1.6;
    }
    
    /* Responsive styling for Mobile viewports */
    @media (max-width: 768px) {
        .hero-headline {
            font-size: 2.0rem !important;
            line-height: 1.3 !important;
        }
        .hero-subheadline {
            font-size: 0.95rem !important;
            line-height: 1.5 !important;
            margin-bottom: 20px !important;
        }
        .glass-card {
            padding: 14px !important;
            margin-bottom: 10px !important;
            border-radius: 12px !important;
        }
        .login-container {
            padding: 20px !important;
            margin: 20px auto !important;
        }
        .stApp h1 {
            font-size: 1.7rem !important;
        }
        .stApp h2 {
            font-size: 1.3rem !important;
        }
        .stApp h3 {
            font-size: 1.15rem !important;
        }
        .stApp h4 {
            font-size: 1.05rem !important;
        }
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
if "show_auth" not in st.session_state:
    st.session_state["show_auth"] = False
if "user_plan" not in st.session_state:
    st.session_state["user_plan"] = "Free"
if "user_selected_mode" not in st.session_state:
    st.session_state["user_selected_mode"] = "Swing Trading Mode"

# Render landing page or login portal if not logged in
if not st.session_state["logged_in"]:
    if st.session_state["show_auth"]:
        # Show Login / Register portal
        col_back_1, col_back_2 = st.columns([5, 1])
        with col_back_2:
            if st.button("⬅️ Halaman Utama", use_container_width=True):
                st.session_state["show_auth"] = False
                st.rerun()
                
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">💸 Smart Saham</div>', unsafe_allow_html=True)
        st.markdown('<div class="premium-badge">✨ PRO SCREENER PORTAL</div>', unsafe_allow_html=True)
        st.markdown("<p style='color:#94a3b8; font-size:0.95rem; margin-top:-10px;'>Akses premium screening saham harian, visualisasi teknikal & histori log berbasis AI-Scoring</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

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
                        # Fetch profile and load into session state
                        profile = storage.get_user_profile(login_username)
                        st.session_state["user_plan"] = profile["plan"]
                        st.session_state["user_selected_mode"] = profile["active_mode"]
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
                - 🛠️ **Dashboard detail & risiko**: Penjelasan alasan status Watchlist Prioritas / Wait and See / Keluar dari Watchlist beserta faktor risikonya.
                - 🗃️ **Sinkronisasi Database Awan**: Histori log tersinkronisasi di Neon DB (PostgreSQL).
                - 🔐 **Log Aktivitas Aman**: Seluruh tindakan terekam aman untuk audit analisis Anda.
                """)
        st.stop()
    else:
        # Show Landing Page
        col_logo_title, col_logo_btn = st.columns([4, 1])
        with col_logo_title:
            st.title("👑 Smart Saham Premium")
            st.caption("AI Stock Screening & Risk Monitoring Platform Bursa Efek Indonesia")
        with col_logo_btn:
            st.write("")
            if st.button("🔐 Masuk ke Aplikasi", use_container_width=True, type="primary"):
                st.session_state["show_auth"] = True
                st.rerun()
                
        # 1 & 2. Hero Section & Subheadline
        st.markdown("""
        <div class="hero-container">
            <h1 class="hero-headline">Analisa Saham Lebih Cepat,<br>Lebih Terarah, dan Berbasis Data.</h1>
            <p class="hero-subheadline">Pilih mode <b>Scalping</b>, <b>Swing Trading</b>, atau <b>Investment</b>. Dapatkan stock score, risk level, alasan sinyal, entry area, target, dan invalidation point dalam satu dashboard.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 3. Main CTA
        col_cta1, col_cta2, col_cta3 = st.columns([1, 2, 1])
        with col_cta2:
            if st.button("🎁 Coba Lihat 3 Saham Berskor Tertinggi Hari Ini (Gratis)", use_container_width=True, type="primary"):
                st.toast("Silakan gulir ke bawah ke bagian Free Signal Preview!", icon="👇")
            if st.button("🔐 Login Premium untuk Akses Watchlist Hari Ini", use_container_width=True):
                st.session_state["show_auth"] = True
                st.rerun()
                
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)
        
        # 5. Market Snapshot
        st.subheader("📊 Market Snapshot Hari Ini")
        col_snap1, col_snap2, col_snap3, col_snap4 = st.columns(4)
        with col_snap1:
            st.markdown("""
            <div class="metric-grid-card" style="border-top: 4px solid #10b981;">
                <div class="metric-grid-lbl">Tren IHSG</div>
                <div class="metric-grid-val" style="color:#10b981;">Neutral to Bullish 🟢</div>
            </div>
            """, unsafe_allow_html=True)
        with col_snap2:
            st.markdown("""
            <div class="metric-grid-card" style="border-top: 4px solid #f59e0b;">
                <div class="metric-grid-lbl">Market Risk Level</div>
                <div class="metric-grid-val" style="color:#f59e0b;">Medium Risk 🟡</div>
            </div>
            """, unsafe_allow_html=True)
        with col_snap3:
            st.markdown("""
            <div class="metric-grid-card" style="border-top: 4px solid #3b82f6;">
                <div class="metric-grid-lbl">Sektor Terkuat</div>
                <div class="metric-grid-val" style="color:#3b82f6;">Financials & Energy</div>
            </div>
            """, unsafe_allow_html=True)
        with col_snap4:
            st.markdown("""
            <div class="metric-grid-card" style="border-top: 4px solid #8b5cf6;">
                <div class="metric-grid-lbl">Best Mode Today</div>
                <div class="metric-grid-val" style="color:#8b5cf6;">Swing Trading Mode</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # 6. 3 Cards Mode
        st.subheader("💡 3 Mode Analisis Saham Utama")
        st.markdown("<p style='color:#94a3b8; margin-top:-10px;'>Pilih gaya analisa Anda, setiap mode memiliki parameter indikator dan kalkulasi skor khusus:</p>", unsafe_allow_html=True)
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.markdown("""
            <div class="glass-card" style="border-top: 4px solid #ef4444; min-height: 260px;">
                <h4 style="color:#ef4444; margin-top:0;">⏱️ Scalping Mode</h4>
                <p style="color:#cbd5e1; font-size:0.88rem; line-height:1.5;">Dirancang untuk perdagangan jangka sangat pendek (hitungan menit s/d 1 hari). Menganalisis momentum intraday harian di atas VWAP, lonjakan volume intraday, spread bid-ask ketat, dan rasio ketebalan Bid vs Ask order book secara live.</p>
            </div>
            """, unsafe_allow_html=True)
        with col_c2:
            st.markdown("""
            <div class="glass-card" style="border-top: 4px solid #3b82f6; min-height: 260px;">
                <h4 style="color:#3b82f6; margin-top:0;">📈 Swing Trading Mode</h4>
                <p style="color:#cbd5e1; font-size:0.88rem; line-height:1.5;">Dirancang untuk perdagangan jangka pendek s/d menengah (2 hari s/d 30 hari). Fokus mendeteksi pembalikan tren harian (pullback) atau penembusan resistance (breakout) di atas MA20/MA50 didukung data Bandarmologi harian.</p>
            </div>
            """, unsafe_allow_html=True)
        with col_c3:
            st.markdown("""
            <div class="glass-card" style="border-top: 4px solid #10b981; min-height: 260px;">
                <h4 style="color:#10b981; margin-top:0;">🏢 Investment Mode</h4>
                <p style="color:#cbd5e1; font-size:0.88rem; line-height:1.5;">Dirancang untuk investasi jangka panjang (6 bulan+). Menghitung nilai wajar intrinsik (Graham Fair Value) berbasis earning yield (ROE/ROE), tingkat beban utang (DER), stabilitas arus kas operasional (OCF) dan Margin of Safety.</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 4. Preview Dashboard
        st.subheader("🖥️ Pratinjau Dashboard & Hasil Screening")
        st.markdown("<p style='color:#94a3b8; margin-top:-10px;'>Potongan tampilan leaderboard real-time dengan beberapa detail parameter penting dikunci untuk akun Free:</p>", unsafe_allow_html=True)
        
        mock_data = [
            {"Ticker": "BBCA.JK", "Mode": "Investment Mode", "Final Score": 82, "Signal": "Investasi Prioritas", "Risk Level": "Low", "Entry Area": "Rp 8,800 - Rp 9,000", "Target Profit": "Rp 9,800 (TP1)", "Stop Loss": "Rp 8,400"},
            {"Ticker": "BBRI.JK", "Mode": "Swing Trading Mode", "Final Score": 85, "Signal": "Swing Prioritas", "Risk Level": "Low", "Entry Area": "Rp 4,450 - Rp 4,550", "Target Profit": "Rp 4,800 (TP1)", "Stop Loss": "Rp 4,300"},
            {"Ticker": "ADRO.JK", "Mode": "Scalping Mode (Beta)", "Final Score": 78, "Signal": "Scalping Prioritas", "Risk Level": "Medium", "Entry Area": "Rp 2,680 - Rp 2,700", "Target Profit": "Rp 2,740 (TP1)", "Stop Loss": "Rp 2,640"},
            {"Ticker": "TLKM.JK", "Mode": "Swing Trading Mode", "Final Score": 62, "Signal": "Wait and See (Swing)", "Risk Level": "Medium", "Entry Area": "🔒 Login Premium", "Target Profit": "🔒 Login Premium", "Stop Loss": "🔒 Login Premium"},
            {"Ticker": "ASII.JK", "Mode": "Investment Mode", "Final Score": 58, "Signal": "Wait and See (Investasi)", "Risk Level": "Medium", "Entry Area": "🔒 Login Premium", "Target Profit": "🔒 Login Premium", "Stop Loss": "🔒 Login Premium"},
            {"Ticker": "GOTO.JK", "Mode": "Scalping Mode (Beta)", "Final Score": 41, "Signal": "Keluar dari Watchlist (Scalping)", "Risk Level": "High", "Entry Area": "🔒 Login Premium", "Target Profit": "🔒 Login Premium", "Stop Loss": "🔒 Login Premium"},
        ]
        df_mock = pd.DataFrame(mock_data)
        st.dataframe(df_mock, use_container_width=True, hide_index=True)
        st.caption("🔒 *Detail area beli (entry), target profit, stop loss, dan analisis lengkap untuk emiten lainnya disamarkan. Silakan login untuk membuka data lengkap.*")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # 7. Free Signal Preview (3 Free Stocks)
        st.subheader("🎁 Contoh Hasil Analisis Saham Hari Ini")
        st.markdown("<p style='color:#94a3b8; margin-top:-10px;'>Berikut adalah contoh 3 saham dengan hasil screening score tertinggi hari ini sebagai referensi penelitian mandiri:</p>", unsafe_allow_html=True)
        
        preview_tabs = st.tabs(["📊 Swing Trade: BBRI", "⏱️ Scalping: ADRO", "🏢 Investasi: BBCA"])
        with preview_tabs[0]:
            col_bbri1, col_bbri2 = st.columns([1, 1])
            with col_bbri1:
                st.markdown("""
                <div class="glass-card" style="border-left: 5px solid #10b981; min-height: 250px;">
                    <h3 style="margin-top:0; color:#10b981; font-weight:800;">BBRI.JK</h3>
                    <p style="margin:8px 0;"><b>Mode:</b> Swing Trading Mode</p>
                    <p style="margin:8px 0;"><b>Confidence Score:</b> <span style="font-weight:bold; color:#10b981;">85 / 100</span></p>
                    <p style="margin:8px 0;"><b>Signal:</b> <span class="badge badge-buy">Swing Prioritas</span></p>
                    <p style="margin:8px 0;"><b>Risk Level:</b> Low</p>
                </div>
                """, unsafe_allow_html=True)
            with col_bbri2:
                st.markdown("""
                <div class="glass-card" style="border-left: 5px solid #3b82f6; min-height: 250px;">
                    <h4 style="margin-top:0; color:#3b82f6;">Acuan Parameter Analisis:</h4>
                    <p style="margin:6px 0;"><b>Area Pantau (Support/Pullback):</b> Rp 4,450 - Rp 4,550</p>
                    <p style="margin:6px 0;"><b>Resistansi Terdekat (Target Area):</b> Rp 4,800</p>
                    <p style="margin:6px 0;"><b>Resistansi Lanjutan:</b> Rp 5,100</p>
                    <p style="margin:6px 0;"><b>Batas Invalidation Terdekat:</b> Rp 4,300</p>
                    <p style="margin:6px 0; font-size:0.85rem; color:#cbd5e1;"><b>Reasoning:</b> Volume transaksi harian stabil di atas rata-rata diiringi akumulasi asing beruntun 5 hari terakhir di area support kuat MA50.</p>
                </div>
                """, unsafe_allow_html=True)
                
        with preview_tabs[1]:
            col_adro1, col_adro2 = st.columns([1, 1])
            with col_adro1:
                st.markdown("""
                <div class="glass-card" style="border-left: 5px solid #f59e0b; min-height: 250px;">
                    <h3 style="margin-top:0; color:#f59e0b; font-weight:800;">ADRO.JK</h3>
                    <p style="margin:8px 0;"><b>Mode:</b> Scalping Mode (Beta)</p>
                    <p style="margin:8px 0;"><b>Confidence Score:</b> <span style="font-weight:bold; color:#f59e0b;">78 / 100</span></p>
                    <p style="margin:8px 0;"><b>Signal:</b> <span class="badge badge-buy">Scalping Prioritas</span></p>
                    <p style="margin:8px 0;"><b>Risk Level:</b> Medium</p>
                </div>
                """, unsafe_allow_html=True)
            with col_adro2:
                st.markdown("""
                <div class="glass-card" style="border-left: 5px solid #3b82f6; min-height: 250px;">
                    <h4 style="margin-top:0; color:#3b82f6;">Acuan Parameter Analisis:</h4>
                    <p style="margin:6px 0;"><b>Area Pantau (Intraday):</b> Rp 2,680 - Rp 2,700</p>
                    <p style="margin:6px 0;"><b>Target Resistansi Intraday 1:</b> Rp 2,740</p>
                    <p style="margin:6px 0;"><b>Target Resistansi Intraday 2:</b> Rp 2,780</p>
                    <p style="margin:6px 0;"><b>Batas Risiko Intraday (Cut Loss):</b> Rp 2,640</p>
                    <p style="margin:6px 0; font-size:0.85rem; color:#cbd5e1;"><b>Reasoning:</b> Lonjakan volume transaksi intraday terdeteksi 2.2x rata-rata dengan harga bergerak konsisten di atas VWAP intraday.</p>
                </div>
                """, unsafe_allow_html=True)
                
        with preview_tabs[2]:
            col_bbca1, col_bbca2 = st.columns([1, 1])
            with col_bbca1:
                st.markdown("""
                <div class="glass-card" style="border-left: 5px solid #10b981; min-height: 250px;">
                    <h3 style="margin-top:0; color:#10b981; font-weight:800;">BBCA.JK</h3>
                    <p style="margin:8px 0;"><b>Mode:</b> Investment Mode</p>
                    <p style="margin:8px 0;"><b>Confidence Score:</b> <span style="font-weight:bold; color:#10b981;">82 / 100</span></p>
                    <p style="margin:8px 0;"><b>Signal:</b> <span class="badge badge-buy">Investasi Prioritas</span></p>
                    <p style="margin:8px 0;"><b>Risk Level:</b> Low</p>
                </div>
                """, unsafe_allow_html=True)
            with col_bbca2:
                st.markdown("""
                <div class="glass-card" style="border-left: 5px solid #3b82f6; min-height: 250px;">
                    <h4 style="margin-top:0; color:#3b82f6;">Pemetaan Estimasi Nilai Wajar:</h4>
                    <p style="margin:6px 0;"><b>Estimasi Rentang Nilai Wajar:</b> Rp 9,400 - Rp 10,800</p>
                    <p style="margin:6px 0;"><b>Margin Keamanan (MOS Estimasi):</b> +6.5%</p>
                    <p style="margin:6px 0;"><b>Profil Risiko Governance:</b> Low</p>
                    <p style="margin:6px 0; font-size:0.85rem; color:#cbd5e1;"><b>Reasoning:</b> Profitabilitas ROE prima (21.5%) dan DER rendah. Harga saat ini berada di bawah rentang nilai intrinsik dengan margin aman positif.</p>
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)
        
        # 8. Kenapa Pakai Aplikasi Ini
        st.subheader("🤔 Kenapa Memilih Smart Saham?")
        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1:
            st.markdown("""
            <div class="glass-card" style="min-height: 180px;">
                <h5 style="margin-top:0;">⚡ Hemat Waktu Analisis</h5>
                <p style="color:#cbd5e1; font-size:0.85rem; line-height:1.5;">Sistem AI-Scoring kami langsung memindai 800+ saham di Bursa Efek Indonesia secara real-time. Tidak perlu memantau chart manual satu per satu.</p>
            </div>
            """, unsafe_allow_html=True)
        with col_w2:
            st.markdown("""
            <div class="glass-card" style="min-height: 180px;">
                <h5 style="margin-top:0;">📊 Berbasis Probabilitas Data</h5>
                <p style="color:#cbd5e1; font-size:0.85rem; line-height:1.5;">Seluruh skor dihitung murni berbasis data historis harga, volume, akumulasi broker (Bandarmologi), dan laporan keuangan resmi. Bukan berdasarkan rumor atau bisikan.</p>
            </div>
            """, unsafe_allow_html=True)
        with col_w3:
            st.markdown("""
            <div class="glass-card" style="min-height: 180px;">
                <h5 style="margin-top:0;">🛡️ Dilengkapi Exit Plan & Risiko</h5>
                <p style="color:#cbd5e1; font-size:0.85rem; line-height:1.5;">Menyediakan visualisasi parameter level risiko (Low/Medium/High), alasan logika sinyal, serta exit plan terukur (Target Profit, Stop Loss, Invalidation Point).</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # 9. Cara Kerja
        st.subheader("🛠️ Bagaimana Cara Kerjanya?")
        col_h1, col_h2, col_h3, col_h4 = st.columns(4)
        with col_h1:
            st.markdown("""
            <div class="glass-card" style="text-align:center; min-height: 200px;">
                <div style="font-size:2.2rem; margin-bottom:10px;">1️⃣</div>
                <h5 style="margin-top:0;">Pilih Mode</h5>
                <p style="color:#cbd5e1; font-size:0.8rem; line-height:1.4;">Tentukan mode analisis yang cocok dengan horizon trading Anda: Scalping, Swing, atau Investasi.</p>
            </div>
            """, unsafe_allow_html=True)
        with col_h2:
            st.markdown("""
            <div class="glass-card" style="text-align:center; min-height: 200px;">
                <div style="font-size:2.2rem; margin-bottom:10px;">2️⃣</div>
                <h5 style="margin-top:0;">Lihat Score</h5>
                <p style="color:#cbd5e1; font-size:0.8rem; line-height:1.4;">Urutkan leaderboard untuk menemukan emiten berskor tertinggi yang memiliki probabilitas terbaik.</p>
            </div>
            """, unsafe_allow_html=True)
        with col_h3:
            st.markdown("""
            <div class="glass-card" style="text-align:center; min-height: 200px;">
                <div style="font-size:2.2rem; margin-bottom:10px;">3️⃣</div>
                <h5 style="margin-top:0;">Pahami Reasoning</h5>
                <p style="color:#cbd5e1; font-size:0.8rem; line-height:1.4;">Pelajari alasan kalkulasi indikator di balik sinyal beserta batasan risiko exit-nya.</p>
            </div>
            """, unsafe_allow_html=True)
        with col_h4:
            st.markdown("""
            <div class="glass-card" style="text-align:center; min-height: 200px;">
                <div style="font-size:2.2rem; margin-bottom:10px;">4️⃣</div>
                <h5 style="margin-top:0;">Track Portofolio</h5>
                <p style="color:#cbd5e1; font-size:0.8rem; line-height:1.4;">Catat entri beli/jual di log transaksi untuk memantau performa akurasi secara berkala.</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)
        
        # 10. Pricing Teaser
        st.subheader("💎 Paket Layanan Smart Saham")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.markdown("""
            <div class="glass-card" style="border-top: 4px solid #94a3b8; min-height: 380px;">
                <h4 style="margin-top:0; color:#94a3b8;">🆓 Paket FREE</h4>
                <h2 style="margin-top:5px; margin-bottom:5px;">Rp 0</h2>
                <p style="color:#64748b; font-size:0.8rem; margin-bottom:15px;">Mencoba Value Awal Aplikasi</p>
                <ul style="color:#cbd5e1; font-size:0.82rem; padding-left:15px; line-height:1.5; margin-top:10px;">
                    <li>Preview 3 saham berskor tertinggi per hari</li>
                    <li>Snapshot tren pasar & IHSG harian</li>
                    <li>Watchlist maksimal 3 saham</li>
                    <li>Log riwayat sinyal maksimal 3 hari</li>
                    <li>❌ Reasoning & parameter entry/exit dikunci</li>
                    <li>❌ Tidak bisa akses grup Telegram Premium</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        with col_p2:
            st.markdown("""
            <div class="glass-card" style="border-top: 4px solid #3b82f6; min-height: 380px;">
                <h4 style="margin-top:0; color:#3b82f6;">📈 Paket 1 MODE</h4>
                <h2 style="margin-top:5px; margin-bottom:5px;">Rp 89.000 <span style="font-size:0.8rem; font-weight:normal; color:#94a3b8;">/ bln</span></h2>
                <p style="color:#64748b; font-size:0.8rem; margin-bottom:15px;">Rp 890.000 / tahun (Hemat 2 bulan)</p>
                <ul style="color:#cbd5e1; font-size:0.82rem; padding-left:15px; line-height:1.5; margin-top:10px;">
                    <li><b>Akses Penuh 1 Mode Pilihan:</b> Scalping, Swing, ATAU Investasi</li>
                    <li>Full reasoning & setup entry/exit mode pilihan</li>
                    <li>Watchlist maksimal 20 saham</li>
                    <li>Log riwayat sinyal hingga 30 hari</li>
                    <li>Simulasi tracking portofolio terbatas</li>
                    <li><b>Bisa join grup Telegram Premium</b></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        with col_p3:
            st.markdown("""
            <div class="glass-card" style="border-top: 4px solid #f59e0b; min-height: 380px; background: rgba(245, 158, 11, 0.03);">
                <h4 style="margin-top:0; color:#f59e0b;">👑 ALL MODE <span style="background-color:#d97706; color:#ffffff; font-size:0.7rem; padding:2px 8px; border-radius:10px; font-weight:bold; margin-left:5px; text-transform:uppercase;">Best Value</span></h4>
                <h2 style="margin-top:5px; margin-bottom:5px; color:#f59e0b;">Rp 179.000 <span style="font-size:0.8rem; font-weight:normal; color:#94a3b8;">/ bln</span></h2>
                <p style="color:#64748b; font-size:0.8rem; margin-bottom:15px;">Rp 1.790.000 / tahun (Hemat 2 bulan)</p>
                <ul style="color:#cbd5e1; font-size:0.82rem; padding-left:15px; line-height:1.5; margin-top:10px;">
                    <li><b>Akses Penuh Ke Seluruh Mode Analisis</b> (Scalping, Swing, & Investasi)</li>
                    <li>Full reasoning & setup entry/exit semua mode</li>
                    <li>Watchlist Tanpa Batas (Unlimited)</li>
                    <li>Log riwayat sinyal penuh hingga 90 hari</li>
                    <li>Simulasi tracking portofolio tanpa batas</li>
                    <li><b>Bisa join grup Telegram Premium</b></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Bottom final CTA to toggle show_auth
        st.markdown("""
        <div class="login-container" style="max-width: 100%; padding: 40px; margin-top:20px;">
            <h3 style="margin-top:0;">Siap Mengambil Keputusan Investasi Berbasis Data?</h3>
            <p style="color:#94a3b8; font-size:1.05rem;">Dapatkan akses instan ke 3 saham berskor tertinggi hari ini secara gratis.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col_bt1, col_bt2, col_bt3 = st.columns([1, 2, 1])
        with col_bt2:
            if st.button("🔐 Masuk ke Akun Premium / Buat Akun Baru Sekarang", use_container_width=True, type="primary"):
                st.session_state["show_auth"] = True
                st.rerun()
                
        st.write("")
        st.write("")
        st.markdown("<center><p style='color:#64748b; font-size:0.78rem; line-height:1.5;'>⚠️ <b>Disclaimer Regulasi (OJK)</b>: Smart Saham Premium adalah platform screening data & risk monitoring berbasis probabilitas analisis data historis saham. Aplikasi ini bukan platform pemberi rekomendasi final atau ajakan beli/jual investasi. Seluruh keputusan finansial berada di bawah tanggung jawab pribadi Anda secara mandiri.</p></center>", unsafe_allow_html=True)
        st.stop()

# ----------------- LOGGED IN APPLICATION INTERFACE -----------------

# Header area with Welcome message and Logout
col_header_title, col_header_user = st.columns([3, 1])
with col_header_title:
    st.title("👑 Smart Saham Premium Dashboard")
    st.markdown("##### *AI Stock Screening & Risk Monitoring Platform Bursa Efek Indonesia*")
    with st.expander("⚠️ Disclaimer Hukum & Regulasi OJK", expanded=False):
        st.caption("Aplikasi ini bukan platform pemberi rekomendasi investasi final untuk beli/jual saham, melainkan platform penyaring data (*AI Stock Screening*) & pemantauan risiko (*Risk Monitoring*) untuk membantu riset mandiri Anda.")
with col_header_user:
    st.write("")
    is_admin = st.session_state["username"] == "fra"
    role_label = "Admin" if is_admin else "Customer"
    st.markdown(f"👤 Akun: **{st.session_state['username'].upper()}** `({role_label})`")
    
    # Plan Simulator Selector (Compact & Clean)
    with st.expander("👤 Status & Paket Layanan", expanded=True):
        sim_plan = st.selectbox(
            "Simulasi Paket:",
            options=["Free Plan", "1 Mode Plan", "All Mode Plan"],
            index=0 if st.session_state["user_plan"] == "Free" else (1 if st.session_state["user_plan"] == "1 Mode" else 2),
            key="header_plan_sim"
        )
        
        # Sync to session state
        new_plan = "Free"
        if sim_plan == "1 Mode Plan":
            new_plan = "1 Mode"
        elif sim_plan == "All Mode Plan":
            new_plan = "All Mode"
            
        new_mode = st.session_state["user_selected_mode"]
            
        # Select active mode for 1 Mode
        if new_plan == "1 Mode":
            sim_unlocked = st.selectbox(
                "Pilih Mode Aktif Anda:",
                options=["Swing Trading Mode", "Scalping Mode (Beta)", "Investment Mode"],
                index=["Swing Trading Mode", "Scalping Mode (Beta)", "Investment Mode"].index(st.session_state["user_selected_mode"]),
                key="header_mode_sim"
            )
            new_mode = sim_unlocked
            
        # Detect changes and save persistently to DB
        if (new_plan != st.session_state["user_plan"]) or (new_plan == "1 Mode" and new_mode != st.session_state["user_selected_mode"]):
            # Update DB/CSV
            storage.update_user_profile(st.session_state["username"], new_plan, new_mode)
            # Update session state
            st.session_state["user_plan"] = new_plan
            st.session_state["user_selected_mode"] = new_mode
            st.toast("💾 Paket terupdate secara permanen di database!", icon="✅")
            st.rerun()
            
        st.caption(f"Paket Aktif: **{st.session_state['user_plan']}**")
        if st.session_state["user_plan"] == "1 Mode":
            st.caption(f"Mode Unlocked: **{st.session_state['user_selected_mode']}**")
        
    if st.button("🚪 Keluar Akun (Logout)", use_container_width=True):
        storage.log_activity(st.session_state["username"], "LOGOUT")
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["show_auth"] = False
        st.rerun()

st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)

# Grid Layout for Options - 2 Columns instead of 3
col_cfg1, col_cfg2 = st.columns(2)
with col_cfg1:
    selected_preset = st.selectbox(
        "🎯 Preset Kategori Saham:",
        options=[
            "Kustom (Pilih Manual)", 
            "Ketik Ticker Manual",
            "Semua Saham IDX (820+ Emiten)", 
            "Saham Syariah (JII70 - Liquid)",
            "Semua Saham Syariah (600+ Emiten)",
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
        ],
        help="Pilih kelompok preset saham yang ingin Anda saring datanya."
    )
with col_cfg2:
    selected_mode = st.selectbox(
        "📈 Mode Analisis Saham:",
        options=["Swing Trading Mode", "Scalping Mode (Beta)", "Investment Mode"],
        help="Memilih model analisa, horizon investasi, parameter scoring, dan visualisasi dashboard."
    )

# Internally default historical period to 1 year as requested
history_period = "1y"

selected_tickers = []

if selected_preset == "Kustom (Pilih Manual)":
    selected_tickers = st.multiselect(
        "Pilih Saham (Bisa multi-select):",
        options=list(IDX_STOCKS.keys()),
        default=["BBRI.JK"],
        format_func=lambda x: f"{x.split('.')[0]} - {IDX_STOCKS.get(x, x)}"
    )
elif selected_preset == "Ketik Ticker Manual":
    ticker_input = st.text_input("Ketik ticker saham (pisahkan dengan koma):", "BBNI, ANTM, PTBA")
    tickers_list = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
    formatted_tickers = []
    for t in tickers_list:
        if not t.endswith(".JK"):
            t = f"{t}.JK"
        formatted_tickers.append(t)
    selected_tickers = formatted_tickers
elif selected_preset == "Semua Saham IDX (820+ Emiten)":
    selected_tickers = list(IDX_STOCKS.keys())
    st.warning("⚠️ Menganalisis 820+ saham sekaligus memerlukan waktu sekitar 1-2 menit. Klik tombol Jalankan Analisis di bawah.")
elif selected_preset == "Saham Syariah (JII70 - Liquid)":
    selected_tickers = [t for t in IDX_JII70_TICKERS if t in IDX_STOCKS]
    st.info(f"Terpilih {len(selected_tickers)} saham syariah likuid (Jakarta Islamic Index 70).")
elif selected_preset == "Semua Saham Syariah (600+ Emiten)":
    df_stocks_db = load_stock_database_df()
    sharia_df = df_stocks_db[df_stocks_db.apply(lambda r: is_sharia_compliant(r['ticker'], r['name']), axis=1)]
    selected_tickers = sharia_df['ticker'].tolist()
    st.warning(f"⚠️ Terpilih {len(selected_tickers)} saham syariah di IDX. Menganalisis kelompok besar ini memerlukan waktu ~1 menit. Klik tombol di bawah.")
else:
    sector_name = selected_preset.replace("Sektor ", "")
    if "(" in sector_name and ")" in sector_name:
        sector_name = sector_name.split("(")[1].split(")")[0]
    
    df_stocks_db = load_stock_database_df()
    df_sector = df_stocks_db[df_stocks_db['sector'] == sector_name]
    selected_tickers = df_sector['ticker'].tolist()
    st.info(f"Terpilih {len(selected_tickers)} saham di {selected_preset}.")

# Setup automated configuration triggers without manual buttons

# Telegram & DB configurations (Collapsible Expander)
tg_bot_token = ""
tg_chat_id = ""
auto_send_buy = False

try:
    tg_bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
    tg_chat_id = st.secrets.get("TELEGRAM_CHAT_ID", "")
except Exception:
    pass
    
is_admin = st.session_state["username"] == "fra"

if is_admin:
    with st.expander("⚙️ Pengaturan Lanjutan (Status DB & Telegram Bot Alert)", expanded=False):
        col_adv1, col_adv2 = st.columns(2)
        with col_adv1:
            st.markdown("🌐 **Status Sinkronisasi Database**")
            if db_url:
                st.success("Terkoneksi ke Neon DB Cloud (PostgreSQL)")
            else:
                st.info("Koneksi Database: Lokal (SQLite/CSV)")
        with col_adv2:
            st.markdown("🔔 **Konfigurasi Telegram Bot (Admin Only)**")
            tg_bot_token = st.text_input("Bot Token", value=tg_bot_token, type="password", help="API Token Bot Telegram")
            tg_chat_id = st.text_input("Group/Chat ID", value=tg_chat_id, placeholder="Contoh: -100123456789")
            auto_send_buy = st.checkbox("Auto-Send Sinyal Watchlist Prioritas", value=False)

st.markdown("---")

# ----------------- CONTROLLER / STOCK PROCESSING PIPELINE -----------------

# Track selected tickers and period in session state to auto-run when changed
if "last_selected_tickers" not in st.session_state:
    st.session_state["last_selected_tickers"] = []
if "last_history_period" not in st.session_state:
    st.session_state["last_history_period"] = "1y"
if "last_selected_mode" not in st.session_state:
    st.session_state["last_selected_mode"] = "Swing Trading Mode"

tickers_changed = set(selected_tickers) != set(st.session_state["last_selected_tickers"])
period_changed = history_period != st.session_state["last_history_period"]
mode_changed = selected_mode != st.session_state["last_selected_mode"]

should_trigger = False

if "results" not in st.session_state:
    if selected_tickers:
        should_trigger = True
elif tickers_changed or period_changed or mode_changed:
    should_trigger = True

if "results" not in st.session_state and not should_trigger:
    st.info("💡 **Silakan pilih kategori saham atau mode analisis di atas** untuk memulai screening secara otomatis.")

if should_trigger:
    st.session_state["last_selected_tickers"] = selected_tickers
    st.session_state["last_history_period"] = history_period
    st.session_state["last_selected_mode"] = selected_mode
    
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
            
            # Import specific scoring methods
            from src.scoring import calculate_scalping_score, calculate_swing_score, calculate_investment_score
            
            # Branch scoring based on selected mode
            intraday_df = pd.DataFrame()
            order_book = {}
            financials = {}
            
            if selected_mode == "Scalping Mode (Beta)":
                intraday_df = loader.fetch_intraday_data(ticker)
                order_book = loader.fetch_order_book(ticker)
                score_data = calculate_scalping_score(indicators, intraday_df, order_book)
                score_data["technical_score"] = score_data["score"]
                score_data["flow_score"] = score_data["score"]
                score_data["final_score"] = score_data["score"]
                score_data["flow_data"] = {"data_status": "Intraday & Order Book Live Simulator"}
            elif selected_mode == "Investment Mode":
                financials = loader.fetch_financials_and_valuation(ticker)
                score_data = calculate_investment_score(financials, close_price)
                score_data["technical_score"] = score_data["score"]
                score_data["flow_score"] = score_data["score"]
                score_data["final_score"] = score_data["score"]
                score_data["flow_data"] = {"data_status": "Laporan Keuangan & Fundamental"}
            else: # Swing Trading Mode
                score_data = calculate_swing_score(indicators, df_broker, df_foreign)
                score_data["technical_score"] = score_data["score"]
                score_data["flow_score"] = score_data["score"]
                score_data["final_score"] = score_data["score"]
                score_data["flow_data"] = {
                    "foreign_net_1d": 0.0 if df_foreign is None or df_foreign.empty else float(df_foreign.sort_values('date', ascending=False).iloc[0]['foreign_net_value']),
                    "foreign_net_5d": 0.0 if df_foreign is None or df_foreign.empty else float(df_foreign.sort_values('date', ascending=False).head(5)['foreign_net_value'].sum()),
                    "foreign_net_20d": 0.0 if df_foreign is None or df_foreign.empty else float(df_foreign.sort_values('date', ascending=False).head(20)['foreign_net_value'].sum()),
                    "data_status": "Koneksi Bandarmologi Aktif"
                }
            
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
                "score": score_data["final_score"], 
                "recommendation": score_data["recommendation"], 
                "reasons": score_data["reasons"],
                "risks": score_data["risks"],
                "entry_area": score_data.get("entry_area", "N/A"),
                "tp1": score_data.get("tp1", "N/A"),
                "tp2": score_data.get("tp2", "N/A"),
                "sl": score_data.get("sl", "N/A"),
                "risk_reward_ratio": score_data.get("risk_reward_ratio", "N/A"),
                "entry_reason": score_data.get("entry_reason", score_data["reasons"][0] if score_data["reasons"] else "Analisis Multi-Mode"),
                "invalidation_point": score_data.get("invalidation_point", "N/A"),
                "risk_level": score_data.get("risk_level", "Medium"),
                "time_horizon": score_data.get("time_horizon", "N/A"),
                "fair_value_range": score_data.get("fair_value_range", "N/A"),
                "margin_of_safety": score_data.get("margin_of_safety", "N/A"),
                
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
                "df_foreign": df_foreign,
                "intraday_df": intraday_df,
                "order_book": order_book,
                "financials": financials,
                "mode": selected_mode
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
                
            # Auto-send Watchlist Prioritas alerts to Telegram
            if auto_send_buy and tg_bot_token and tg_chat_id:
                sent_count = 0
                for r in all_results:
                    if r["recommendation"] in ["BUY", "Watchlist Prioritas"]:
                        success, msg = send_telegram_alert(tg_bot_token, tg_chat_id, r)
                        if success:
                            sent_count += 1
                if sent_count > 0:
                    st.toast(f"🔔 Berhasil mengirim {sent_count} alert sinyal Watchlist Prioritas ke Telegram!", icon="🚀")
        else:
            st.error("Tidak ada saham yang berhasil dianalisis. Harap pastikan format ticker benar (contoh: BBCA.JK atau BBCA).")

# ----------------- VIEW LAYER: RENDER DASHBOARD CONTENTS -----------------

if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]
    histories = st.session_state["histories"]
    
    if "saved_status" in st.session_state:
        st.caption(st.session_state["saved_status"])
        
    is_admin = st.session_state["username"] == "fra"
    
    if is_admin:
        tabs = st.tabs([
            "📊 Screener & Ranking", 
            "📜 Histori Rekomendasi", 
            "💼 Simulasi & Log Portofolio", 
            "📢 Telegram Paid Group",
            "🎨 Share Card & Laporan",
            "🔐 Audit Aktivitas User (Neon DB)"
        ])
        tab_screener = tabs[0]
        tab_history = tabs[1]
        tab_portfolio = tabs[2]
        tab_telegram = tabs[3]
        tab_social = tabs[4]
        tab_activities = tabs[5]
    else:
        tabs = st.tabs([
            "📊 Screener & Ranking", 
            "📜 Histori Rekomendasi",
            "💼 Simulasi & Log Portofolio", 
            "📢 Telegram Paid Group",
            "🎨 Share Card & Laporan"
        ])
        tab_screener = tabs[0]
        tab_history = tabs[1]
        tab_portfolio = tabs[2]
        tab_telegram = tabs[3]
        tab_social = tabs[4]
    
    with tab_screener:
        # Helper to map signal to regulatory-friendly Indonesian terms
        def clean_signal_name(sig):
            sig_clean = sig.strip()
            if sig_clean in ["Watchlist Prioritas", "BUY", "Scalping Prioritas", "Swing Prioritas", "Investasi Prioritas"]:
                return "Watchlist Prioritas"
            elif sig_clean in ["Wait and See", "HOLD / WATCH", "HOLD", "WATCH", "Wait and See (Scalping)", "Wait and See (Swing)", "Wait and See (Investasi)"]:
                return "Wait and See"
            return "Keluar dari Watchlist"

        # Mode Info Banner
        if selected_mode == "Scalping Mode (Beta)":
            st.info("⏱️ **Mode Scalping (Sinyal Intraday)**\n\n*Mode ini dirancang untuk perdagangan jangka sangat pendek (hitungan menit s/d 1 hari). Fokus analisis berada pada volume transaksi intraday harian, pergerakan harga relatif terhadap VWAP, indikator momentum cepat (EMA9 & EMA21), dan likuiditas kedalaman Bid-Ask Order Book.*")
        elif selected_mode == "Investment Mode":
            st.info("🏢 **Mode Investasi (Fundamental Jangka Panjang)**\n\n*Mode ini dirancang untuk akumulasi aset jangka panjang (6 bulan s/d bertahun-tahun). Fokus utama terletak pada kualitas profitabilitas perusahaan (ROE & Margin), risiko beban utang (DER), pertumbuhan laba bersih, kualitas arus kas, serta perhitungan nilai wajar (Fair Value) dan Margin of Safety (MOS).*")
        else:
            st.info("📈 **Mode Swing Trading (Sinyal Multi-Hari)**\n\n*Mode ini dirancang untuk menangkap pergerakan harga jangka pendek s/d menengah (2 hari s/d 30 hari). Analisis difokuskan pada kekuatan tren harga (MA20 & MA50), kejenuhan RSI, crossover MACD, serta konfirmasi volume harian dan data Bandarmologi (akumulasi asing & 3 broker terbesar).*")

        # Highlights Metrics Layout
        buy_count = sum(1 for r in results if clean_signal_name(r["recommendation"]) == "Watchlist Prioritas")
        watch_count = sum(1 for r in results if clean_signal_name(r["recommendation"]) == "Wait and See")
        avoid_count = sum(1 for r in results if clean_signal_name(r["recommendation"]) == "Keluar dari Watchlist")
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #3b82f6;"><div class="metric-grid-lbl">Saham Di-Screen</div><div class="metric-grid-val" style="color:#3b82f6;">{len(results)}</div></div>', unsafe_allow_html=True)
        with col_m2:
            st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #10b981;"><div class="metric-grid-lbl">Watchlist Prioritas</div><div class="metric-grid-val" style="color:#10b981;">{buy_count}</div></div>', unsafe_allow_html=True)
        with col_m3:
            st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #f59e0b;"><div class="metric-grid-lbl">Wait and See</div><div class="metric-grid-val" style="color:#f59e0b;">{watch_count}</div></div>', unsafe_allow_html=True)
        with col_m4:
            st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #ef4444;"><div class="metric-grid-lbl">Keluar dari Watchlist</div><div class="metric-grid-val" style="color:#ef4444;">{avoid_count}</div></div>', unsafe_allow_html=True)
            
        st.write("")
        col_tbl_title, col_tbl_filter = st.columns([2, 1])
        with col_tbl_title:
            st.subheader("🏆 Leaderboard Hasil Screening Saham")
        with col_tbl_filter:
            signal_filter = st.multiselect(
                "Filter Sinyal:",
                options=["Watchlist Prioritas", "Wait and See", "Keluar dari Watchlist"],
                default=["Watchlist Prioritas", "Wait and See", "Keluar dari Watchlist"]
            )

        table_data = []
        for r in results:
            fd = r["flow_data"]
            clean_rec_sig = clean_signal_name(r["recommendation"])
            
            if selected_mode == "Scalping Mode (Beta)":
                vwap_val = "N/A"
                if "intraday_df" in r and not r["intraday_df"].empty:
                    vwap_val = f"Rp {r['intraday_df'].iloc[-1]['vwap']:,.0f}"
                spread_val = "N/A"
                if "order_book" in r and r["order_book"]:
                    spread_val = f"{r['order_book']['spread']:.2f}%"
                bid_ask_val = "N/A"
                if "order_book" in r and r["order_book"]:
                    bid_ask_val = f"{r['order_book']['bid_ask_ratio']:.2f}x"
                    
                table_data.append({
                    "Ticker": r["ticker"],
                    "Last Price": f"Rp {r['close_price']:,.0f}",
                    "VWAP": vwap_val,
                    "Spread": spread_val,
                    "Bid-Ask Ratio": bid_ask_val,
                    "RSI Intraday": f"{r['rsi']:.1f}" if r['rsi'] is not None else "N/A",
                    "Vol Ratio Intraday": f"{r['volume_ratio']:.2f}x",
                    "Final Score": r["score"],
                    "Signal": r["recommendation"],
                    "Entry Area": r["entry_area"],
                    "SL": f"Rp {r['sl']:,}" if isinstance(r['sl'], (int, float)) else r['sl'],
                    "TP1": f"Rp {r['tp1']:,}" if isinstance(r['tp1'], (int, float)) else r['tp1'],
                    "TP2": f"Rp {r['tp2']:,}" if isinstance(r['tp2'], (int, float)) else r['tp2'],
                    "Risk Level": r["risk_level"]
                })
            elif selected_mode == "Investment Mode":
                fin = r.get("financials", {})
                table_data.append({
                    "Ticker": r["ticker"],
                    "Last Price": f"Rp {r['close_price']:,.0f}",
                    "PER": f"{fin.get('PER', 15.0):.1f}x",
                    "PBV": f"{fin.get('PBV', 1.5):.2f}x",
                    "ROE": f"{fin.get('ROE', 10.0):.1f}%",
                    "DER": f"{fin.get('DER', 1.0):.2f}",
                    "Net Margin": f"{fin.get('net_margin', 10.0):.1f}%",
                    "Fair Value Range": r.get("fair_value_range", "N/A"),
                    "Margin of Safety": r.get("margin_of_safety", "N/A"),
                    "Governance Risk": fin.get("governance_risk", "Low"),
                    "Final Score": r["score"],
                    "Signal": r["recommendation"]
                })
            else: # Swing Trading Mode
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
                    "Risk Note": "; ".join([risk.replace("[Teknikal] ", "").replace("[Flow] ", "").replace("[Sinyal] ", "").replace("[Investasi] ", "").replace("[Scalping] ", "") for risk in r["risks"] if "Tidak ada" not in risk][:2]),
                    "Data Status": fd["data_status"]
                })
            
        df_table = pd.DataFrame(table_data).sort_values(by="Final Score", ascending=False).reset_index(drop=True)
        
        # Apply dynamic signal filtering
        df_table_filtered = df_table[df_table['Signal'].apply(clean_signal_name).isin(signal_filter)].reset_index(drop=True)
        
        # Apply dynamic plan-based masking and row slicing
        is_free = (st.session_state["user_plan"] == "Free")
        is_1_mode = (st.session_state["user_plan"] == "1 Mode")
        user_unlocked_mode = st.session_state.get("user_selected_mode", "Swing Trading Mode")
        
        if is_free:
            # Slice to max 3 stocks
            df_table_filtered = df_table_filtered.head(3).copy()
            # Mask sensitive detail columns
            mask_cols = ["Entry Area", "SL", "TP1", "TP2", "Fair Value Range", "Margin of Safety", "Main Reason", "Risk Reward", "Risk Note"]
            for col in mask_cols:
                if col in df_table_filtered.columns:
                    df_table_filtered[col] = "🔒 Hubungkan Premium"
        elif is_1_mode:
            # Slice to max 20 stocks
            df_table_filtered = df_table_filtered.head(20).copy()
            # If current active screening mode does not match user's purchased mode, mask detail columns
            if selected_mode != user_unlocked_mode:
                mask_cols = ["Entry Area", "SL", "TP1", "TP2", "Fair Value Range", "Margin of Safety", "Main Reason", "Risk Reward", "Risk Note"]
                for col in mask_cols:
                    if col in df_table_filtered.columns:
                        df_table_filtered[col] = "🔒 Buka di All Mode"
        
        def style_recommendation(val):
            val_clean = clean_signal_name(val)
            if val_clean == "Watchlist Prioritas":
                return 'background-color: rgba(16, 185, 129, 0.25); color: #10b981; font-weight: bold; border: 1px solid #10b981;'
            elif val_clean == "Wait and See":
                return 'background-color: rgba(245, 158, 11, 0.25); color: #f59e0b; font-weight: bold; border: 1px solid #f59e0b;'
            elif val_clean == "Keluar dari Watchlist":
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
        
        # Check if current mode is locked for details based on plan
        mode_is_locked = False
        paywall_reason = ""
        
        if is_free:
            mode_is_locked = True
            paywall_reason = "Detail analisis komprehensif, grafik interaktif, setup parameter (entry, target, invalidasi), dan profil risiko lengkap hanya terbuka untuk pelanggan berbayar (1 Mode atau All Mode)."
        elif is_1_mode and selected_mode != user_unlocked_mode:
            mode_is_locked = True
            paywall_reason = f"Mode ini dikunci karena Anda berlangganan paket 1 Mode khusus untuk **{user_unlocked_mode}**. Silakan upgrade ke paket All Mode untuk membuka detail seluruh mode analisis."

        if mode_is_locked:
            st.markdown(f'''
            <div class="glass-card" style="border-top: 4px solid #ef4444; padding:35px; text-align:center; margin-top:15px;">
                <h4 style="color:#ef4444; margin-top:0;">🔒 Fitur Detail Analisis Terkunci</h4>
                <p style="color:#cbd5e1; font-size:0.95rem; line-height:1.5;">{paywall_reason}</p>
            </div>
            ''', unsafe_allow_html=True)
        else:
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

                if selected_mode == "Scalping Mode (Beta)":
                    st.warning("⚠️ **Beta / Limited Mode**: Data intraday disimulasikan dari snapshot harian terakhir karena keterbatasan real-time feed.")
                
                    df_intra = stock_details.get("intraday_df")
                    if df_intra is not None and not df_intra.empty:
                        st.markdown(f"##### ⏱️ Grafik Candle Intraday (5m) & VWAP Line: **{selected_stock}**")
                        fig_intra = go.Figure()
                        # Candlestick
                        fig_intra.add_trace(go.Candlestick(
                            x=df_intra['datetime'],
                            open=df_intra['open'],
                            high=df_intra['high'],
                            low=df_intra['low'],
                            close=df_intra['close'],
                            name="Intraday 5m"
                        ))
                        # EMA9 & EMA21
                        fig_intra.add_trace(go.Scatter(
                            x=df_intra['datetime'], y=df_intra['open'].ewm(span=9).mean(),
                            line=dict(color='#60a5fa', width=1.5), name="EMA 9"
                        ))
                        fig_intra.add_trace(go.Scatter(
                            x=df_intra['datetime'], y=df_intra['open'].ewm(span=21).mean(),
                            line=dict(color='#f59e0b', width=1.5), name="EMA 21"
                        ))
                        # VWAP Line
                        fig_intra.add_trace(go.Scatter(
                            x=df_intra['datetime'], y=df_intra['vwap'],
                            line=dict(color='#e11d48', width=2, dash='dash'), name="VWAP"
                        ))
                        fig_intra.update_layout(
                            template="plotly_dark",
                            xaxis_rangeslider_visible=False,
                            margin=dict(l=20, r=20, t=10, b=10),
                            height=280,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        st.plotly_chart(fig_intra, use_container_width=True)
                    
                    # Render Simulated Order Book Depth
                    ob = stock_details.get("order_book", {})
                    if ob:
                        st.markdown("##### 📖 Kedalaman Buku Order (Bid-Ask Depth)")
                        ob_rows = []
                        for i in range(5):
                            ob_rows.append({
                                "Bid Lot": f"{ob.get(f'bid_lot_{i+1}'):,}",
                                "Bid Price": f"Rp {ob.get(f'bid_price_{i+1}'):,}",
                                "Ask Price": f"Rp {ob.get(f'ask_price_{i+1}'):,}",
                                "Ask Lot": f"{ob.get(f'ask_lot_{i+1}'):,}"
                            })
                        df_ob = pd.DataFrame(ob_rows)
                        st.dataframe(df_ob, use_container_width=True, hide_index=True)
                    
                        st.caption(f"Spread: **{ob.get('spread', 0.0):.2f}%** | Bid-Ask Ratio: **{ob.get('bid_ask_ratio', 1.0):.2f}x** (Total Bid: {ob.get('total_bid_lots'):,} lot / Total Ask: {ob.get('total_ask_lots'):,} lot)")
            
                elif selected_mode == "Investment Mode":
                    fin = stock_details.get("financials", {})
                
                    st.markdown(f"##### 📊 Grafik Valuasi Historis & Rentang Fair Value: **{selected_stock}**")
                    fv_lower = 0.0
                    fv_upper = 0.0
                    if "fair_value_range" in fin:
                        parts = fin["fair_value_range"].replace("Rp ", "").replace(",", "").split(" - ")
                        if len(parts) == 2:
                            fv_lower = float(parts[0])
                            fv_upper = float(parts[1])
                        
                    fig_val = go.Figure()
                    fig_val.add_trace(go.Scatter(
                        x=df_chart['Date'], y=df_chart['Close'],
                        line=dict(color='#3b82f6', width=2), name="Harga Close"
                    ))
                    if fv_lower > 0:
                        fig_val.add_hline(y=fv_lower, line_dash="dash", line_color="#34d399", annotation_text="Fair Value Min")
                        fig_val.add_hline(y=fv_upper, line_dash="dash", line_color="#10b981", annotation_text="Fair Value Max")
                    
                    fig_val.update_layout(
                        template="plotly_dark",
                        margin=dict(l=20, r=20, t=10, b=10),
                        height=280,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_val, use_container_width=True)
                
                    # Financial Statements detail table
                    st.markdown("##### 📰 Ringkasan Neraca & Arus Kas Kuartalan")
                    fin_data = pd.DataFrame([
                        {"Kategori": "Pendapatan (Revenue)", "Nilai": f"Rp {fin.get('revenue', 0.0):,.0f}"},
                        {"Kategori": "Laba Kotor (Gross Profit)", "Nilai": f"Rp {fin.get('gross_profit', 0.0):,.0f}"},
                        {"Kategori": "Laba Bersih (Net Profit)", "Nilai": f"Rp {fin.get('net_profit', 0.0):,.0f}"},
                        {"Kategori": "Total Aset (Assets)", "Nilai": f"Rp {fin.get('total_asset', 0.0):,.0f}"},
                        {"Kategori": "Total Liabilitas (Debt)", "Nilai": f"Rp {fin.get('total_liability', 0.0):,.0f}"},
                        {"Kategori": "Total Ekuitas (Equity)", "Nilai": f"Rp {fin.get('total_equity', 0.0):,.0f}"},
                        {"Kategori": "Arus Kas Operasional (OCF)", "Nilai": f"Rp {fin.get('operating_cash_flow', 0.0):,.0f}"},
                        {"Kategori": "Belanja Modal (Capex)", "Nilai": f"Rp {fin.get('capex', 0.0):,.0f}"}
                    ])
                    st.dataframe(fin_data, use_container_width=True, hide_index=True)
                
                else: # Swing Trading Mode
                    st.markdown(f"##### Grafik Candlestick, MA, & Price Channels (20D Support/Resistance): **{selected_stock}**")
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=df_chart['Date'], open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'],
                        name="Harga Saham", increasing_line_color='#10b981', decreasing_line_color='#ef4444'
                    ))
                    if 'MA20' in df_chart.columns:
                        fig.add_trace(go.Scatter(x=df_chart['Date'], y=df_chart['MA20'], line=dict(color='#3b82f6', width=2), name='MA 20'))
                    if 'MA50' in df_chart.columns:
                        fig.add_trace(go.Scatter(x=df_chart['Date'], y=df_chart['MA50'], line=dict(color='#f59e0b', width=2), name='MA 50'))
                    if 'Support20D' in df_chart.columns:
                        fig.add_trace(go.Scatter(x=df_chart['Date'], y=df_chart['Support20D'], line=dict(color='#ef4444', width=1.5, dash='dash'), name='Support 20D'))
                    if 'Resistance20D' in df_chart.columns:
                        fig.add_trace(go.Scatter(x=df_chart['Date'], y=df_chart['Resistance20D'], line=dict(color='#10b981', width=1.5, dash='dash'), name='Resistance 20D'))
                    
                    fig.update_layout(
                        template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=10, b=10), height=350,
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                    st.markdown(f"##### Volume Transaksi Harian & Rata-rata 20 Hari: **{selected_stock}**")
                    fig_vol = go.Figure()
                    fig_vol.add_trace(go.Bar(x=df_chart['Date'], y=df_chart['Volume'], marker_color='rgba(59, 130, 246, 0.4)', name='Volume Harian'))
                    fig_vol.add_trace(go.Scatter(x=df_chart['Date'], y=df_chart['Vol_MA20'], line=dict(color='#3b82f6', width=2), name='Vol MA20'))
                    fig_vol.update_layout(
                        template="plotly_dark", margin=dict(l=20, r=20, t=10, b=10), height=180,
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_vol, use_container_width=True)
                
                    st.markdown(f"##### Indikator Relative Strength Index (RSI 14): **{selected_stock}**")
                    fig_rsi = go.Figure()
                    fig_rsi.add_trace(go.Scatter(x=df_chart['Date'], y=df_chart['RSI'], line=dict(color='#a78bfa', width=2), fill='tozeroy', fillcolor='rgba(167, 139, 250, 0.05)', name='RSI 14'))
                    fig_rsi.add_hline(y=70, line_dash="dash", line_color="#ef4444", annotation_text="Overbought")
                    fig_rsi.add_hline(y=30, line_dash="dash", line_color="#10b981", annotation_text="Oversold")
                    fig_rsi.update_layout(
                        template="plotly_dark", yaxis=dict(range=[10, 90]), margin=dict(l=20, r=20, t=10, b=10), height=180,
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
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
            
                # Map legacy signal to clean OJK term
                clean_rec = clean_signal_name(rec)
                if clean_rec == "Watchlist Prioritas":
                    rec_badge_style = "badge-buy"
                elif clean_rec == "Wait and See":
                    rec_badge_style = "badge-watch"
                else:
                    rec_badge_style = "badge-avoid"

                st.markdown(f"""
                <div style="margin-top:-20px; margin-bottom:15px;">
                    <span class="badge {rec_badge_style}" style="font-size:1.4rem; padding:8px 25px; border-radius:30px;">
                        {clean_rec}
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
                # Manual Telegram push button (Admin Only)
                if is_admin and tg_bot_token and tg_chat_id:
                    if st.button("📤 Kirim Sinyal Ke Telegram", key="btn_send_tg", use_container_width=True):
                        with st.spinner("Mengirim alert telegram..."):
                            success, msg = send_telegram_alert(tg_bot_token, tg_chat_id, stock_details)
                            if success:
                                st.toast("✅ Sinyal dikirim ke Telegram!", icon="🔔")
                                st.success(msg)
                            else:
                                st.error(msg)
                            
                st.markdown("</div>", unsafe_allow_html=True)
            
                if selected_mode == "Scalping Mode (Beta)":
                    # Combined Grid Score Dashboard
                    st.markdown("##### 🔢 Detail Bobot Penilaian Scalping")
                    st.markdown(f"**Intraday Momentum:** +25% | **Volume Spike:** +20% | **Liquidity:** +20% | **VWAP Position:** +15% | **Order Depth:** +10% | **Broker & Risk:** +10%")
                    st.write("")
                
                    # --- TRADING SIGNAL SETUP SECTION ---
                    st.markdown("##### 🎯 Setup Sinyal Scalping Intraday")
                    st.markdown(f"**Entry Area (Intraday):** <span style='font-size:1.15rem; color:#60a5fa; font-weight:700;'>{stock_details['entry_area']}</span>", unsafe_allow_html=True)
                
                    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                    with col_s1:
                        tp1_val = f"Rp {stock_details['tp1']:,}" if isinstance(stock_details['tp1'], (int, float)) else stock_details['tp1']
                        st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Target 1 (1.5%)</div><div class="metric-grid-val" style="color:#34d399; font-size:1.1rem; padding-top:4px;">{tp1_val}</div></div>', unsafe_allow_html=True)
                    with col_s2:
                        tp2_val = f"Rp {stock_details['tp2']:,}" if isinstance(stock_details['tp2'], (int, float)) else stock_details['tp2']
                        st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Target 2 (3%)</div><div class="metric-grid-val" style="color:#10b981; font-size:1.1rem; padding-top:4px;">{tp2_val}</div></div>', unsafe_allow_html=True)
                    with col_s3:
                        sl_val = f"Rp {stock_details['sl']:,}" if isinstance(stock_details['sl'], (int, float)) else stock_details['sl']
                        st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Stop Loss</div><div class="metric-grid-val" style="color:#f87171; font-size:1.1rem; padding-top:4px;">{sl_val}</div></div>', unsafe_allow_html=True)
                    with col_s4:
                        st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Horizon</div><div class="metric-grid-val" style="font-size:1.1rem; padding-top:4px; color:#a78bfa;">Intraday</div></div>', unsafe_allow_html=True)
                
                    st.write("")
                    st.markdown(f"💡 **Titik Invalidasi:** {stock_details['invalidation_point']}")
                
                elif selected_mode == "Investment Mode":
                    fin = stock_details.get("financials", {})
                    st.markdown("##### 🔢 Detail Bobot Penilaian Investasi")
                    st.markdown(f"**Business Quality:** +20% | **Revenue/Earnings Growth:** +20% | **Profitability:** +15% | **Balance Sheet:** +15% | **Cash Flow:** +10% | **Valuation:** +10% | **Others:** +10%")
                
                    st.write("")
                    st.markdown("##### 🎯 Hasil Evaluasi Investasi Jangka Panjang")
                
                    col_inv1, col_inv2 = st.columns(2)
                    with col_inv1:
                        st.markdown(f"**Kualitas Bisnis:** `{stock_details.get('quality_status', 'Average')}`")
                        st.markdown(f"**Valuasi Saham:** `{stock_details.get('valuation_status', 'Fair')}`")
                        st.markdown(f"**Pertumbuhan Bisnis:** `{stock_details.get('growth_status', 'Stagnant')}`")
                    with col_inv2:
                        st.markdown(f"**Rasio Utang (DER):** `{fin.get('DER', 1.0):.2f} ({stock_details.get('debt_risk', 'Medium')})`")
                        st.markdown(f"**Kualitas Arus Kas:** `{stock_details.get('cash_flow_quality', 'Good')}`")
                        st.markdown(f"**Governance Risk:** `{fin.get('governance_risk', 'Low')}`")
                    
                    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
                    col_mos1, col_mos2 = st.columns(2)
                    with col_mos1:
                        st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Rentang Fair Value</div><div class="metric-grid-val" style="color:#60a5fa; font-size:1.1rem; padding-top:4px;">{stock_details.get("fair_value_range", "N/A")}</div></div>', unsafe_allow_html=True)
                    with col_mos2:
                        st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Margin of Safety</div><div class="metric-grid-val" style="color:#10b981; font-size:1.1rem; padding-top:4px;">{stock_details.get("margin_of_safety", "N/A")}</div></div>', unsafe_allow_html=True)
                
                    st.write("")
                    st.markdown(f"💡 **Titik Invalidasi Thesis:** {stock_details['invalidation_point']}")
                
                else: # Swing Trading Mode
                    # Combined Grid Score Dashboard
                    st.markdown("##### 🔢 Detail Bobot Penilaian Swing")
                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Skor Teknikal (60%)</div><div class="metric-grid-val" style="color:#60a5fa;">{stock_details["technical_score"]}</div></div>', unsafe_allow_html=True)
                    with col_t2:
                        flow_s_val = f"{stock_details['flow_score']}" if stock_details['flow_score'] is not None else "N/A"
                        st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Skor Flow (40%)</div><div class="metric-grid-val" style="color:#a78bfa;">{flow_s_val}</div></div>', unsafe_allow_html=True)
                    
                    st.write("")
                
                    # --- TRADING SIGNAL SETUP SECTION ---
                    st.markdown("##### 🎯 Setup Sinyal Swing Trading")
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
                    st.markdown(f"💡 **Titik Invalidasi:** {stock_details['invalidation_point']}")
                
                    # Bandarmologi summary section
                    st.markdown("##### 🐳 Hasil Analisis Bandarmologi & Flow")
                    fd = stock_details["flow_data"]
                    if stock_details["flow_score"] is None:
                        st.warning("⚠️ Data bandarmologi tidak tersedia.")
                    else:
                        col_f1, col_f2, col_f3 = st.columns(3)
                        with col_f1:
                            f_net_1d = fd.get("foreign_net_1d", 0.0)
                            f_color = "#10b981" if f_net_1d > 0 else "#ef4444"
                            st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Foreign 1D</div><div class="metric-grid-val" style="color:{f_color}; font-size:1.0rem;">Rp {f_net_1d/1e9:+.1f}B</div></div>', unsafe_allow_html=True)
                        with col_f2:
                            f_net_5d = fd.get("foreign_net_5d", 0.0)
                            f_color = "#10b981" if f_net_5d > 0 else "#ef4444"
                            st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Foreign 5D</div><div class="metric-grid-val" style="color:{f_color}; font-size:1.0rem;">Rp {f_net_5d/1e9:+.1f}B</div></div>', unsafe_allow_html=True)
                        with col_f3:
                            f_net_20d = fd.get("foreign_net_20d", 0.0)
                            f_color = "#10b981" if f_net_20d > 0 else "#ef4444"
                            st.markdown(f'<div class="metric-grid-card"><div class="metric-grid-lbl">Foreign 20D</div><div class="metric-grid-val" style="color:{f_color}; font-size:1.0rem;">Rp {f_net_20d/1e9:+.1f}B</div></div>', unsafe_allow_html=True)
                        
                        st.write("")
                        st.markdown(f"**Top Buyer Brokers:** {fd.get('top_buyer_brokers', 'N/A')} (Accumulation: `{fd.get('broker_accumulation_signal', 'Neutral')}`)")
                        st.markdown(f"**Top Seller Brokers:** {fd.get('top_seller_brokers', 'N/A')} (Distribution: `{fd.get('broker_distribution_signal', 'Neutral')}`)")
                    
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
        
        # Calculate limits based on active plan
        is_free = (st.session_state["user_plan"] == "Free")
        is_1_mode = (st.session_state["user_plan"] == "1 Mode")
        limit_days = 3 if is_free else (30 if is_1_mode else 90)
        
        st.write(f"Histori data screening harian. Paket Anda ({st.session_state['user_plan']}) membatasi tampilan hingga **{limit_days} hari terakhir**.")
        
        try:
            # Load historical logs
            df_logs = storage.load_historical_logs(limit=1000)
            if not df_logs.empty:
                df_logs['tanggal'] = pd.to_datetime(df_logs['tanggal']).dt.date
                
                # Filter by date range limit
                from datetime import timedelta
                min_date = date.today() - timedelta(days=limit_days)
                df_logs = df_logs[df_logs['tanggal'] >= min_date].reset_index(drop=True)
                
                if not df_logs.empty:
                    df_logs = df_logs.rename(columns={
                        'tanggal': 'Tanggal', 'ticker': 'Ticker', 'close_price': 'Harga Close',
                        'rsi': 'RSI', 'ma20': 'MA 20', 'ma50': 'MA 50', 'momentum_1m': 'Momentum 1M',
                        'momentum_3m': 'Momentum 3M', 'volume_ratio': 'Vol Ratio', 'score': 'Skor',
                        'recommendation': 'Rekomendasi'
                    })
                    st.dataframe(df_logs, use_container_width=True, hide_index=True)
                else:
                    st.info(f"Tidak ada data screening tercatat dalam {limit_days} hari terakhir.")
            else:
                st.info("Log database masih kosong.")
        except Exception as e:
            st.error(f"Gagal memuat log data dari database: {str(e)}")
            

    with tab_portfolio:
        st.header("💼 Simulasi & Log Pemantauan Portofolio Mandiri")
        st.write("Fitur ini dirancang bagi pengguna untuk melakukan log simulasi, melacak keputusan mandiri, serta mengevaluasi secara objektif akurasi screening platform. Catatan ini murni merupakan log transaksi mandiri pengguna untuk pemantauan risiko personal.")
        
        # 1. Automatic/Manual Evaluation Trigger on load
        if "portfolio_evaluated" not in st.session_state:
            with st.spinner("Mengupdate harga portofolio & akurasi sinyal..."):
                run_portfolio_evaluation(storage, loader, st.session_state["username"])
                st.session_state["portfolio_evaluated"] = True
                
        if st.button("🔄 Segarkan Data & Update Evaluasi Harga Terbaru", key="btn_eval_refresh", use_container_width=True):
            with st.spinner("Mengunduh harga historis & mengkalkulasi ulang data portofolio..."):
                run_portfolio_evaluation(storage, loader, st.session_state["username"])
                st.toast("Portofolio berhasil diupdate!", icon="✅")
                
        # Get data
        df_watch = storage.get_watchlist(st.session_state["username"])
        df_eval = storage.get_trade_evaluations(st.session_state["username"])
        
        # 2. ADD TO WATCHLIST OR REAL BUY FORM
        st.subheader("➕ Catat Log Transaksi Mandiri (Simulasi / Pantauan Riil)")
        col_add1, col_add2 = st.columns(2)
        with col_add1:
            screened_tickers_list = [r["ticker"] for r in results] if "results" in st.session_state else []
            selected_add_ticker = st.selectbox(
                "Pilih Saham Hasil Screen:",
                options=["(Pilih Ticker)"] + screened_tickers_list + list(IDX_STOCKS.keys()),
                key="sel_add_ticker"
            )
            user_notes_add = st.text_input("Catatan Tambahan User:", "", key="txt_add_notes")
            
        with col_add2:
            if selected_add_ticker != "(Pilih Ticker)":
                # Find or fetch snapshot score details
                ticker_score_data = None
                if "results" in st.session_state:
                    ticker_score_data = next((r for r in results if r["ticker"] == selected_add_ticker), None)
                
                if not ticker_score_data:
                    df_h = loader.fetch_historical_data(selected_add_ticker, period="1y")
                    if df_h is not None and not df_h.empty:
                        ind = calculate_technical_indicators(df_h)
                        if ind:
                            q = loader.fetch_latest_quote(selected_add_ticker)
                            cl = q.get("currentPrice", ind["close"])
                            ind["close"] = cl
                            df_br = loader.fetch_broker_summary(selected_add_ticker)
                            df_fr = loader.fetch_foreign_flow(selected_add_ticker)
                            
                            if selected_mode == "Scalping Mode (Beta)":
                                intraday_df = loader.fetch_intraday_data(selected_add_ticker)
                                order_book = loader.fetch_order_book(selected_add_ticker)
                                from src.scoring import calculate_scalping_score
                                ticker_score_data = calculate_scalping_score(ind, intraday_df, order_book)
                            elif selected_mode == "Investment Mode":
                                financials = loader.fetch_financials_and_valuation(selected_add_ticker)
                                from src.scoring import calculate_investment_score
                                ticker_score_data = calculate_investment_score(financials, cl)
                            else:
                                from src.scoring import calculate_swing_score
                                ticker_score_data = calculate_swing_score(ind, df_br, df_fr)
                                
                            ticker_score_data["ticker"] = selected_add_ticker
                            ticker_score_data["close_price"] = cl
                            
                if ticker_score_data:
                    if "score" in ticker_score_data and "final_score" not in ticker_score_data:
                        ticker_score_data["final_score"] = ticker_score_data["score"]
                    elif "final_score" in ticker_score_data and "score" not in ticker_score_data:
                        ticker_score_data["score"] = ticker_score_data["final_score"]
                        
                    clean_rec_info = clean_signal_name(ticker_score_data['recommendation'])
                    st.info(f"Sinyal Aktif: **{clean_rec_info}** | Skor Akhir: **{ticker_score_data['final_score']}** | Harga: **Rp {ticker_score_data.get('close_price', 0):,.0f}**")
                    
                    col_btn_add1, col_btn_add2 = st.columns(2)
                    with col_btn_add1:
                        # Watchlist addition plan-based limits
                        allowed_to_add = True
                        if is_free and len(df_watch) >= 3:
                            allowed_to_add = False
                            st.error("🔒 Batas Watchlist Tercapai: Akun Free dibatasi maksimal 3 saham. Silakan upgrade ke paid plan.")
                        elif is_1_mode and len(df_watch) >= 20:
                            allowed_to_add = False
                            st.error("🔒 Batas Watchlist Tercapai: Akun 1 Mode dibatasi maksimal 20 saham. Silakan upgrade ke All Mode.")
                            
                        if st.button("⭐ Add to Watchlist", use_container_width=True, disabled=not allowed_to_add):
                            added = storage.add_to_watchlist(
                                st.session_state["username"],
                                selected_add_ticker,
                                ticker_score_data["recommendation"],
                                ticker_score_data["final_score"],
                                user_notes_add
                            )
                            if added:
                                st.toast(f"✅ {selected_add_ticker} ditambahkan ke Watchlist!", icon="⭐")
                                st.rerun()
                    with col_btn_add2:
                        if is_free:
                            st.info("🔒 Fitur Terkunci: Simulasi portofolio hanya terbuka untuk paid user (1 Mode / All Mode).")
                        else:
                            # 1 Mode limits to 5 total transactions
                            portfolio_locked = False
                            if is_1_mode and len(df_eval) >= 5:
                                portfolio_locked = True
                                st.error("🔒 Batas Transaksi Tercapai: Akun 1 Mode dibatasi maksimal 5 transaksi. Silakan upgrade ke All Mode.")
                                
                            with st.expander("💸 Catat Log Pembelian Mandiri (Simulasi/Riil)", expanded=False):
                                buy_date_input = st.date_input("Tanggal Beli:", date.today())
                                buy_price_input = st.number_input("Harga Beli (Rp):", value=float(ticker_score_data.get('close_price', 0)), step=10.0)
                                lot_qty_input = st.number_input("Jumlah Lot:", value=1, min_value=1, step=1)
                                buy_mode_input = st.selectbox(
                                    "Mode Transaksi:",
                                    options=["Swing Trading Mode", "Scalping Mode (Beta)", "Investment Mode"],
                                    index=["Swing Trading Mode", "Scalping Mode (Beta)", "Investment Mode"].index(selected_mode)
                                )
                                
                                if st.button("💸 Simpan Catatan Pembelian", use_container_width=True, disabled=portfolio_locked):
                                    saved_trade = storage.add_real_trade(
                                        st.session_state["username"],
                                        selected_add_ticker,
                                        buy_date_input,
                                        buy_price_input,
                                        lot_qty_input,
                                        ticker_score_data,
                                        user_notes_add,
                                        analysis_mode=buy_mode_input
                                    )
                                    if saved_trade:
                                        st.toast(f"💸 Log Pembelian Mandiri {selected_add_ticker} berhasil dicatat!", icon="✅")
                                        if "portfolio_evaluated" in st.session_state:
                                            del st.session_state["portfolio_evaluated"]
                                        st.rerun()
                                    
        # 3. WATCHLIST TABLE
        col_w1, col_w2 = st.columns([2, 1])
        with col_w1:
            st.subheader("⭐ Watchlist Saham Anda")
            if not df_watch.empty:
                st.dataframe(df_watch[["ticker", "added_date", "app_signal_when_added", "final_score_when_added", "notes"]].rename(columns={
                    "ticker": "Ticker",
                    "added_date": "Tanggal Ditambahkan",
                    "app_signal_when_added": "Sinyal Saat Ditambah",
                    "final_score_when_added": "Skor Saat Ditambah",
                    "notes": "Catatan"
                }), use_container_width=True, hide_index=True)
            else:
                st.info("Watchlist Anda kosong. Pilih saham di atas untuk memantau pergerakan harganya.")
        with col_w2:
            st.subheader("⚙️ Atur Watchlist")
            if not df_watch.empty:
                sel_w_ticker = st.selectbox("Pilih Saham Watchlist:", options=df_watch["ticker"].tolist(), key="sel_w_ticker")
                if st.button("❌ Remove Watchlist", use_container_width=True):
                    removed = storage.remove_from_watchlist(st.session_state["username"], sel_w_ticker)
                    if removed:
                        st.toast(f"Watchlist {sel_w_ticker} dihapus!", icon="🗑️")
                        st.rerun()
            else:
                st.caption("Tidak ada saham watchlist aktif.")
                
        # 4. PORTFOLIO AND OPEN POSITIONS
        df_open = df_eval[df_eval['status'] == 'Open Position'] if not df_eval.empty else pd.DataFrame()
        df_closed = df_eval[df_eval['status'] == 'Closed Position'] if not df_eval.empty else pd.DataFrame()
        
        st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)
        st.subheader("💼 Simulasi Posisi Terbuka (Open Positions)")
        
        if not df_open.empty:
            df_open_disp = pd.DataFrame({
                "ID": df_open["trade_id"],
                "Ticker": df_open["ticker"],
                "Tanggal Entry": df_open["buy_date"],
                "Harga Entry": df_open["buy_price"].apply(lambda x: f"Rp {x:,.0f}"),
                "Lot": df_open["lot_quantity"],
                "Simulasi Modal": df_open["total_value"].apply(lambda x: f"Rp {x:,.0f}"),
                "Harga Saat Ini": df_open["current_price"].apply(lambda x: f"Rp {x:,.0f}" if pd.notna(x) else "N/A"),
                "Unrealized P/L": df_open["unrealized_profit_loss"].apply(lambda x: f"Rp {x:+,.0f}" if pd.notna(x) else "N/A"),
                "Return (%)": df_open["return_percentage"].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A"),
                "Sinyal Screening": df_open["app_signal_at_buy"].apply(clean_signal_name),
                "TP1 / TP2": df_open.apply(lambda r: f"Rp {r['tp1_at_buy']:,} / Rp {r['tp2_at_buy']:,}", axis=1),
                "Stop Loss": df_open["sl_at_buy"].apply(lambda x: f"Rp {x:,.0f}"),
                "Holding Days": df_open["holding_days"],
                "Catatan": df_open["user_notes"]
            })
            st.dataframe(df_open_disp, use_container_width=True, hide_index=True)
            
            # --- MARK AS SELL / EXIT FORM ---
            st.write("")
            with st.expander("🚪 Catat Keluar Posisi / Simulasi Exit", expanded=False):
                col_exit1, col_exit2 = st.columns(2)
                with col_exit1:
                    exit_trade_id = st.selectbox(
                        "Pilih Posisi Terbuka:",
                        options=df_open["trade_id"].tolist(),
                        format_func=lambda x: f"{df_open[df_open['trade_id'] == x]['ticker'].values[0]} (Entry di Rp {df_open[df_open['trade_id'] == x]['buy_price'].values[0]:,})"
                    )
                    sell_date_input = st.date_input("Tanggal Exit:", date.today(), key="sell_date_inp")
                    sell_price_input = st.number_input("Harga Exit (Rp):", min_value=1.0, step=10.0, key="sell_price_inp")
                with col_exit2:
                    exit_type_input = st.selectbox(
                        "Tipe Exit / Penjualan:",
                        options=["Target Profit 1 Tercapai", "Target Profit 2 Tercapai", "Stop Loss Terlewati", "Exit Mandiri", "Batas Waktu Simulasi", "Sinyal Berubah", "Lainnya"]
                    )
                    sell_reason_input = st.text_input("Alasan Exit (Opsional):", "")
                    
                    if st.button("🚪 Simpan Exit Posisi", use_container_width=True):
                        sold = storage.sell_real_trade(
                            exit_trade_id,
                            sell_date_input,
                            sell_price_input,
                            sell_reason_input,
                            exit_type_input
                        )
                        if sold:
                            st.toast("🚪 Penjualan posisi berhasil dicatat!", icon="✅")
                                  # 5. PERFORMANCE AND ACCURACY DASHBOARD SUMMARY
        st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)
        st.subheader("📈 Analisis Performa & Akurasi Screening")
        
        if not df_eval.empty:
            if "analysis_mode" not in df_eval.columns:
                df_eval["analysis_mode"] = "Swing Trading Mode"
            else:
                df_eval["analysis_mode"] = df_eval["analysis_mode"].fillna("Swing Trading Mode")
                
            total_real_buy = len(df_eval)
            open_count = len(df_open)
            closed_count = len(df_closed)
            
            winning_trades = df_eval[df_eval["return_percentage"] > 0]
            losing_trades = df_eval[df_eval["return_percentage"] < 0]
            
            win_rate = (len(winning_trades) / closed_count * 100) if closed_count > 0 else 0.0
            
            total_realized_pl = df_closed["realized_profit_loss"].sum() if not df_closed.empty else 0.0
            total_unrealized_pl = df_open["unrealized_profit_loss"].sum() if not df_open.empty else 0.0
            
            avg_return = df_eval["return_percentage"].mean()
            median_return = df_eval["return_percentage"].median()
            
            best_trade_val = df_eval["return_percentage"].max()
            best_trade_ticker = df_eval[df_eval["return_percentage"] == best_trade_val]["ticker"].values[0] if not df_eval.empty else "N/A"
            
            worst_trade_val = df_eval["return_percentage"].min()
            worst_trade_ticker = df_eval[df_eval["return_percentage"] == worst_trade_val]["ticker"].values[0] if not df_eval.empty else "N/A"
            
            tp1_hits = int(df_eval["tp1_hit"].sum())
            sl_hits = int(df_eval["sl_hit"].sum())
            tp1_hit_rate = (tp1_hits / total_real_buy * 100) if total_real_buy > 0 else 0.0
            sl_hit_rate = (sl_hits / total_real_buy * 100) if total_real_buy > 0 else 0.0
            
            # Sub-tabs for the stats
            stat_tabs = st.tabs(["📊 Ringkasan Portofolio", "📐 Metrik Berdasarkan Mode", "📈 Analisis Sektoral & Sinyal"])
            
            with stat_tabs[0]:
                # Render KPI
                col_k1, col_k2, col_k3, col_k4 = st.columns(4)
                with col_k1:
                    st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #60a5fa;"><div class="metric-grid-lbl">Total Real Buy</div><div class="metric-grid-val">{total_real_buy}</div><div style="font-size:0.75rem; color:#94a3b8;">{open_count} Open | {closed_count} Closed</div></div>', unsafe_allow_html=True)
                    st.write("")
                    st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #10b981;"><div class="metric-grid-lbl">Total Realized P/L</div><div class="metric-grid-val" style="color:{"#10b981" if total_realized_pl >= 0 else "#ef4444"}; font-size:1.25rem;">Rp {total_realized_pl:+,.0f}</div></div>', unsafe_allow_html=True)
                with col_k2:
                    win_color = "#10b981" if win_rate >= 50 else "#f59e0b"
                    st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid {win_color};"><div class="metric-grid-lbl">Win Rate (Closed)</div><div class="metric-grid-val" style="color:{win_color};">{win_rate:.1f}%</div><div style="font-size:0.75rem; color:#94a3b8;">{len(winning_trades)} Win | {len(losing_trades)} Loss</div></div>', unsafe_allow_html=True)
                    st.write("")
                    st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #a78bfa;"><div class="metric-grid-lbl">Total Unrealized P/L</div><div class="metric-grid-val" style="color:{"#10b981" if total_unrealized_pl >= 0 else "#ef4444"}; font-size:1.25rem;">Rp {total_unrealized_pl:+,.0f}</div></div>', unsafe_allow_html=True)
                with col_k3:
                    ret_color = "#10b981" if avg_return >= 0 else "#ef4444"
                    st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid {ret_color};"><div class="metric-grid-lbl">Average Return</div><div class="metric-grid-val" style="color:{ret_color};">{avg_return:+.2f}%</div><div style="font-size:0.75rem; color:#94a3b8;">Median: {median_return:+.1f}%</div></div>', unsafe_allow_html=True)
                    st.write("")
                    st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #34d399;"><div class="metric-grid-lbl">TP1 Hit Rate</div><div class="metric-grid-val" style="color:#34d399;">{tp1_hit_rate:.1f}%</div><div style="font-size:0.75rem; color:#94a3b8;">{tp1_hits} dari {total_real_buy} kali</div></div>', unsafe_allow_html=True)
                with col_k4:
                    st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #34d399;"><div class="metric-grid-lbl">Best Trade</div><div class="metric-grid-val" style="color:#10b981; font-size:1.2rem;">{best_trade_ticker} ({best_trade_val:+.1f}%)</div></div>', unsafe_allow_html=True)
                    st.write("")
                    st.markdown(f'<div class="metric-grid-card" style="border-top: 4px solid #ef4444;"><div class="metric-grid-lbl">SL Hit Rate</div><div class="metric-grid-val" style="color:#ef4444;">{sl_hit_rate:.1f}%</div><div style="font-size:0.75rem; color:#94a3b8;">{sl_hits} dari {total_real_buy} kali</div></div>', unsafe_allow_html=True)
                    
                st.write("")
                
                # --- CHARTS AND STATS GRID ---
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    st.markdown("##### 📈 Kurva Ekuitas Kumulatif (Equity Curve)")
                    if not df_closed.empty:
                        df_closed_sorted = df_closed.sort_values("sell_date")
                        df_closed_sorted["cum_return"] = df_closed_sorted["return_percentage"].cumsum()
                        
                        fig_eq = go.Figure()
                        fig_eq.add_trace(go.Scatter(
                            x=df_closed_sorted["sell_date"],
                            y=df_closed_sorted["cum_return"],
                            mode='lines+markers',
                            line=dict(color='#10b981', width=3),
                            marker=dict(size=8, color='#34d399'),
                            fill='tozeroy',
                            fillcolor='rgba(16, 185, 129, 0.05)',
                            name="Return Kumulatif (%)"
                        ))
                        fig_eq.update_layout(
                            template="plotly_dark",
                            margin=dict(l=20, r=20, t=10, b=10),
                            height=220,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_eq, use_container_width=True)
                    else:
                        st.info("Kurva ekuitas akan muncul setelah ada minimal satu transaksi yang ditutup (Closed Position).")
                        
                    # Return by Signal Type
                    st.markdown("##### 🚥 Rata-rata Return berdasarkan Sinyal Beli")
                    df_eval_chart = df_eval.copy()
                    df_eval_chart["app_signal_at_buy"] = df_eval_chart["app_signal_at_buy"].apply(clean_signal_name)
                    ret_by_sig = df_eval_chart.groupby("app_signal_at_buy")["return_percentage"].mean().reset_index()
                    
                    colors = ['#10b981' if x == "Watchlist Prioritas" else ('#f59e0b' if x == "Wait and See" else '#ef4444') for x in ret_by_sig["app_signal_at_buy"]]
                    fig_sig = go.Figure(go.Bar(
                        x=ret_by_sig["app_signal_at_buy"],
                        y=ret_by_sig["return_percentage"],
                        marker_color=colors
                    ))
                    fig_sig.update_layout(
                        template="plotly_dark",
                        margin=dict(l=20, r=20, t=10, b=10),
                        height=200,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_sig, use_container_width=True)
                    
                with col_chart2:
                    # Return by ticker
                    st.markdown("##### 📊 Return per Ticker Saham (%)")
                    ret_by_ticker = df_eval.groupby("ticker")["return_percentage"].mean().reset_index()
                    fig_tick = go.Figure(go.Bar(
                        x=ret_by_ticker["ticker"],
                        y=ret_by_ticker["return_percentage"],
                        marker_color='#60a5fa'
                    ))
                    fig_tick.update_layout(
                        template="plotly_dark",
                        margin=dict(l=20, r=20, t=10, b=10),
                        height=220,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_tick, use_container_width=True)
                    
                    # Return by Score Bucket
                    st.markdown("##### 🔢 Rata-rata Return berdasarkan Rentang Skor Final")
                    def get_bucket(score):
                        if score >= 90: return "90-100"
                        elif score >= 80: return "80-89"
                        elif score >= 70: return "70-79"
                        elif score >= 60: return "60-69"
                        else: return "<60"
                    df_eval["score_bucket"] = df_eval["final_score_at_buy"].apply(get_bucket)
                    ret_by_bucket = df_eval.groupby("score_bucket")["return_percentage"].mean().reindex(["90-100", "80-89", "70-79", "60-69", "<60"]).reset_index().dropna()
                    
                    fig_buck = go.Figure(go.Bar(
                        x=ret_by_bucket["score_bucket"],
                        y=ret_by_bucket["return_percentage"],
                        marker_color='#a78bfa'
                    ))
                    fig_buck.update_layout(
                        template="plotly_dark",
                        margin=dict(l=20, r=20, t=10, b=10),
                        height=200,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_buck, use_container_width=True)

            with stat_tabs[1]:
                st.markdown("##### 📐 Perbandingan Performa & Akurasi per Mode Analisis")
                
                modes = ["Swing Trading Mode", "Scalping Mode (Beta)", "Investment Mode"]
                col_m1, col_m2, col_m3 = st.columns(3)
                
                for idx, m in enumerate(modes):
                    df_m = df_eval[df_eval["analysis_mode"] == m]
                    df_m_closed = df_m[df_m["status"] == 'Closed Position']
                    df_m_open = df_m[df_m["status"] == 'Open Position']
                    
                    m_total = len(df_m)
                    m_closed = len(df_m_closed)
                    
                    m_winning = df_m_closed[df_m_closed["return_percentage"] > 0]
                    m_losing = df_m_closed[df_m_closed["return_percentage"] < 0]
                    m_win_rate = (len(m_winning) / m_closed * 100) if m_closed > 0 else 0.0
                    m_avg_ret = df_m["return_percentage"].mean() if not df_m.empty else 0.0
                    
                    m_realized = df_m_closed["realized_profit_loss"].sum() if not df_m_closed.empty else 0.0
                    m_unrealized = df_m_open["unrealized_profit_loss"].sum() if not df_m_open.empty else 0.0
                    
                    gains = df_m_closed[df_m_closed["return_percentage"] > 0]["realized_profit_loss"].sum()
                    losses = abs(df_m_closed[df_m_closed["return_percentage"] < 0]["realized_profit_loss"].sum())
                    m_profit_factor = (gains / losses) if losses > 0 else (gains if gains > 0 else 1.0)
                    m_pf_str = f"{m_profit_factor:.2f}x" if losses > 0 else ("Inf" if gains > 0 else "N/A")
                    
                    target_col = [col_m1, col_m2, col_m3][idx]
                    
                    with target_col:
                        mode_color = "#3b82f6" if idx == 0 else ("#f59e0b" if idx == 1 else "#10b981")
                        st.markdown(f"""
                        <div class="glass-card" style="border-top: 4px solid {mode_color}; padding: 15px; border-radius: 12px; margin-bottom:15px;">
                            <h4 style="margin-top: 0; color: {mode_color};">{m}</h4>
                            <p style="margin: 5px 0;"><b>Total Trades:</b> {m_total} ({len(df_m_open)} Open | {m_closed} Closed)</p>
                            <p style="margin: 5px 0;"><b>Win Rate:</b> <span style="color: {'#10b981' if m_win_rate >= 50 else '#f59e0b'}; font-weight:bold;">{m_win_rate:.1f}%</span></p>
                            <p style="margin: 5px 0;"><b>Profit Factor:</b> {m_pf_str}</p>
                            <p style="margin: 5px 0;"><b>Avg Return:</b> <span style="color: {'#10b981' if m_avg_ret >= 0 else '#ef4444'}; font-weight:bold;">{m_avg_ret:+.2f}%</span></p>
                            <p style="margin: 5px 0; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 5px;"><b>Realized P/L:</b> Rp {m_realized:+,.0f}</p>
                            <p style="margin: 5px 0;"><b>Unrealized P/L:</b> Rp {m_unrealized:+,.0f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
            with stat_tabs[2]:
                st.markdown("##### 🔍 Analisis Sektoral, Akurasi Sinyal, & Profit Factor")
                
                df_stocks_db = load_stock_database_df()
                best_sector_str = "N/A"
                worst_sector_str = "N/A"
                
                if not df_stocks_db.empty and not df_closed.empty:
                    df_eval_with_sector = df_eval.merge(df_stocks_db[["ticker", "sector"]], on="ticker", how="left")
                    df_eval_with_sector["sector"] = df_eval_with_sector["sector"].fillna("Lainnya")
                    sector_perf = df_eval_with_sector[df_eval_with_sector["status"] == "Closed Position"].groupby("sector")["return_percentage"].mean().reset_index()
                    
                    if not sector_perf.empty:
                        best_sec = sector_perf.loc[sector_perf["return_percentage"].idxmax()]
                        worst_sec = sector_perf.loc[sector_perf["return_percentage"].idxmin()]
                        best_sector_str = f"🟢 **{best_sec['sector']}** ({best_sec['return_percentage']:+.2f}%)"
                        worst_sector_str = f"🔴 **{worst_sec['sector']}** ({worst_sec['return_percentage']:+.2f}%)"
                
                best_sig_str = "N/A"
                worst_sig_str = "N/A"
                sig_accuracy = []
                
                unique_sigs = df_eval["app_signal_at_buy"].unique()
                for sig in unique_sigs:
                    df_sig = df_eval[df_eval["app_signal_at_buy"] == sig]
                    tot_sig = len(df_sig)
                    if tot_sig > 0:
                        correct_sig = len(df_sig[df_sig["prediction_result"] == "Correct"])
                        acc = (correct_sig / tot_sig) * 100
                        sig_accuracy.append({
                            "signal": clean_signal_name(sig),
                            "accuracy": acc,
                            "total": tot_sig
                        })
                df_sig_acc = pd.DataFrame(sig_accuracy)
                if not df_sig_acc.empty:
                    df_sig_acc_sorted = df_sig_acc.sort_values(by="accuracy", ascending=False)
                    best_row = df_sig_acc_sorted.iloc[0]
                    worst_row = df_sig_acc_sorted.iloc[-1]
                    best_sig_str = f"🟢 **{best_row['signal']}** ({best_row['accuracy']:.1f}% Akurasi dari {best_row['total']} kali)"
                    worst_sig_str = f"🔴 **{worst_row['signal']}** ({worst_row['accuracy']:.1f}% Akurasi dari {worst_row['total']} kali)"
                
                total_gains = df_closed[df_closed["return_percentage"] > 0]["realized_profit_loss"].sum()
                total_losses = abs(df_closed[df_closed["return_percentage"] < 0]["realized_profit_loss"].sum())
                overall_profit_factor = (total_gains / total_losses) if total_losses > 0 else (total_gains if total_gains > 0 else 1.0)
                overall_pf_str = f"{overall_profit_factor:.2f}x" if total_losses > 0 else ("Inf" if total_gains > 0 else "N/A")
                
                col_an1, col_an2 = st.columns(2)
                with col_an1:
                    st.markdown("##### 🏢 Kinerja Sektoral Portofolio")
                    st.markdown(f"**Sektor Terbaik (Best Performing):** {best_sector_str}")
                    st.markdown(f"**Sektor Terburuk (Worst Performing):** {worst_sector_str}")
                    
                    st.write("")
                    st.markdown("##### 📢 Akurasi Sinyal Platform")
                    st.markdown(f"**Sinyal Paling Akurat (Best Signal):** {best_sig_str}")
                    st.markdown(f"**Sinyal Paling Sering Gagal:** {worst_sig_str}")
                
                with col_an2:
                    st.markdown("##### 🎯 Metrik Risiko & Profitabilitas")
                    st.markdown(f"**Total Profit Factor (Portofolio):** **{overall_pf_str}**")
                    avg_win = winning_trades["return_percentage"].mean() if len(winning_trades) > 0 else 0.0
                    avg_loss = losing_trades["return_percentage"].mean() if len(losing_trades) > 0 else 0.0
                    st.markdown(f"**Average Profit (Winning Trades):** <span style='color:#10b981; font-weight:bold;'>{avg_win:+.2f}%</span>", unsafe_allow_html=True)
                    st.markdown(f"**Average Loss (Losing Trades):** <span style='color:#ef4444; font-weight:bold;'>{avg_loss:+.2f}%</span>", unsafe_allow_html=True)
                    
                st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)
                st.subheader("🎯 Detail Hasil Akurasi Screening")
                
                pred_summary = df_eval.groupby("prediction_result").size().reset_index(name="count")
                col_acc1, col_acc2 = st.columns([1, 2])
                with col_acc1:
                    fig_pie = go.Figure(go.Pie(
                        labels=pred_summary["prediction_result"],
                        values=pred_summary["count"],
                        hole=0.4,
                        marker=dict(colors=['#10b981' if x == "Correct" else ('#ef4444' if x == "Wrong" else '#94a3b8') for x in pred_summary["prediction_result"]])
                    ))
                    fig_pie.update_layout(
                        template="plotly_dark",
                        margin=dict(l=10, r=10, t=10, b=10),
                        height=180,
                        paper_bgcolor='rgba(0,0,0,0)',
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2)
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                with col_acc2:
                    for _, row in df_eval.iterrows():
                        res_class = row["prediction_result"]
                        color_tag = "🟢" if res_class == "Correct" else ("🔴" if res_class == "Wrong" else "⚪")
                        sig_name = clean_signal_name(row['app_signal_at_buy'])
                        st.markdown(f"{color_tag} **{row['ticker']}** (Screening Sinyal `{sig_name}`): {row['prediction_result_detail']}")
            
            # --- TRADE JOURNAL SECTION ---
            st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)
            st.subheader("📓 Jurnal Transaksi (Trade Journal)")
            
            col_f_j1, col_f_j2, col_f_j3 = st.columns(3)
            with col_f_j1:
                j_ticker_filter = st.multiselect("Filter Ticker Saham:", options=df_eval["ticker"].unique())
            with col_f_j2:
                j_status_filter = st.selectbox("Filter Status Posisi:", options=["Semua", "Open Position", "Closed Position"])
            with col_f_j3:
                j_signal_filter = st.selectbox("Filter Sinyal Saat Beli:", options=["Semua", "Watchlist Prioritas", "Wait and See", "Keluar dari Watchlist"])
                
            df_j_filtered = df_eval.copy()
            if j_ticker_filter:
                df_j_filtered = df_j_filtered[df_j_filtered["ticker"].isin(j_ticker_filter)]
            if j_status_filter != "Semua":
                df_j_filtered = df_j_filtered[df_j_filtered["status"] == j_status_filter]
            if j_signal_filter != "Semua":
                df_j_filtered = df_j_filtered[df_j_filtered["app_signal_at_buy"].apply(clean_signal_name) == j_signal_filter]
                
            df_journal_table = pd.DataFrame({
                "Ticker": df_j_filtered["ticker"],
                "Tgl Beli": df_j_filtered["buy_date"],
                "Harga Beli": df_j_filtered["buy_price"].apply(lambda x: f"Rp {x:,.0f}"),
                "Current Price": df_j_filtered["current_price"].apply(lambda x: f"Rp {x:,.0f}" if pd.notna(x) else "N/A"),
                "Tgl Jual": df_j_filtered["sell_date"].apply(lambda x: str(x) if pd.notna(x) else "N/A"),
                "Harga Jual": df_j_filtered["sell_price"].apply(lambda x: f"Rp {x:,.0f}" if pd.notna(x) else "N/A"),
                "Status": df_j_filtered["status"],
                "Sinyal Screening": df_j_filtered["app_signal_at_buy"].apply(clean_signal_name),
                "Skor Beli": df_j_filtered["final_score_at_buy"],
                "Return (%)": df_j_filtered["return_percentage"].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A"),
                "Realized P/L": df_j_filtered["realized_profit_loss"].apply(lambda x: f"Rp {x:+,.0f}" if pd.notna(x) else "N/A"),
                "Unrealized P/L": df_j_filtered["unrealized_profit_loss"].apply(lambda x: f"Rp {x:+,.0f}" if pd.notna(x) else "N/A"),
                "Holding Days": df_j_filtered["holding_days"],
                "Exit Type": df_j_filtered["exit_type"].apply(lambda x: str(x) if pd.notna(x) else "N/A"),
                "Catatan": df_j_filtered["user_notes"]
            }).reset_index(drop=True)
            
            st.dataframe(df_journal_table, use_container_width=True, hide_index=True)
            
            # --- EXPORT BUTTONS ---
            col_exp1, col_exp2, col_exp3 = st.columns(3)
            with col_exp1:
                st.download_button(
                    label="📥 Export Jurnal ke CSV",
                    data=df_eval.to_csv(index=False),
                    file_name="trade_journal_export.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_exp2:
                acc_summary = pd.DataFrame([{
                    "Total Real Buy": total_real_buy,
                    "Open Positions": open_count,
                    "Closed Positions": closed_count,
                    "Win Rate (%)": win_rate,
                    "Average Return (%)": avg_return,
                    "TP1 Hit Rate (%)": tp1_hit_rate,
                    "SL Hit Rate (%)": sl_hit_rate
                }])
                st.download_button(
                    label="📥 Export Akurasi ke CSV",
                    data=acc_summary.to_csv(index=False),
                    file_name="accuracy_summary.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_exp3:
                st.download_button(
                    label="📥 Export Performa Sinyal ke CSV",
                    data=ret_by_sig.to_csv(index=False),
                    file_name="performance_by_signal.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    with tab_telegram:
        st.header("📢 Smart Saham Premium Telegram Group")
        st.write("Akses ke grup Telegram Premium eksklusif untuk mendapatkan notifikasi instan langsung di handphone Anda.")
        
        # Check active plan
        is_free = (st.session_state["user_plan"] == "Free")
        
        if is_free:
            st.markdown("""
            <div class="glass-card" style="border-top: 4px solid #ef4444; padding:35px; text-align:center; margin-top:20px; margin-bottom:20px;">
                <h3 style="color:#ef4444; margin-top:0;">🔒 Grup Telegram Premium Terkunci</h3>
                <p style="color:#cbd5e1; font-size:1.0rem;">Grup Telegram Premium hanya tersedia untuk pengguna berbayar (paket 1 Mode atau All Mode).</p>
                <p style="color:#94a3b8; font-size:0.85rem; margin-bottom:20px;">Dapatkan alert sinyal instan, market update, weekly recap, dan diskusi edukatif di grup eksklusif kami.</p>
            </div>
            """, unsafe_allow_html=True)
            st.button("👑 Hubungkan Premium (Upgrade ke 1 Mode / All Mode)", key="tg_tab_upgrade_btn", use_container_width=True)
        else:
            st.markdown(f"""
            <div class="glass-card" style="border-top: 4px solid #10b981; padding:35px; text-align:center; margin-top:20px; margin-bottom:20px;">
                <h3 style="color:#10b981; margin-top:0;">🎉 Akses Grup Telegram Premium Aktif!</h3>
                <p style="color:#cbd5e1; font-size:1.0rem;">Sebagai pelanggan berbayar (<b>{st.session_state["user_plan"]}</b>), Anda memiliki hak akses penuh ke <b>Smart Saham Premium Telegram Group</b>.</p>
                <p style="color:#94a3b8; font-size:0.85rem; margin-bottom:25px;">Nikmati alert sinyal otomatis, pembaruan sektoral, weekly recap, dan edukasi singkat yang sama untuk seluruh member paid.</p>
            </div>
            """, unsafe_allow_html=True)
            st.link_button("💬 Gabung ke Grup Telegram Premium", url="https://t.me/joinchat/mock_premium_group_link", use_container_width=True)

    with tab_social:
        st.header("📢 Social Share Card & Exit Report")
        st.write("Generate kartu performa visual (Share Card) formal yang elegan untuk transaksi yang sudah ditutup (*Closed Position*). Kartu ini dapat diunduh atau dikirim langsung ke grup Telegram.")
        
        df_eval_social = storage.get_trade_evaluations(st.session_state["username"])
        
        if not df_eval_social.empty:
            selected_social_id = st.selectbox(
                "Pilih Transaksi untuk Di-Share:",
                options=df_eval_social["trade_id"].tolist(),
                format_func=lambda x: f"{df_eval_social[df_eval_social['trade_id'] == x]['ticker'].values[0]} | Status: {df_eval_social[df_eval_social['trade_id'] == x]['status'].values[0]} | ROI: {df_eval_social[df_eval_social['trade_id'] == x]['return_percentage'].values[0]:+.2f}%",
                key="sel_social_trade_id"
            )
            
            trade_data_social = df_eval_social[df_eval_social["trade_id"] == selected_social_id].iloc[0].to_dict()
            
            # Check if trade status is Closed Position
            if trade_data_social["status"] != "Closed Position":
                st.warning("⚠️ Trade belum exit, share card final belum bisa dibuat.")
            else:
                col_sc_sel, col_sc_act = st.columns([1, 1])
                with col_sc_sel:
                    # Template and Size ratio selectors
                    social_template = st.selectbox(
                        "Pilih Desain Template:",
                        options=["Formal Dark", "Formal Light", "Executive Summary"]
                    )
                    
                    social_ratio = st.selectbox(
                        "Pilih Ukuran Gambar (Rasio):",
                        options=["1080x1080 (Square Instagram Feed)", "1080x1920 (Instagram Story)", "1200x628 (Telegram Preview)"]
                    )
                    
                    ratio_value = "1080x1080"
                    if "1920" in social_ratio:
                        ratio_value = "1080x1920"
                    elif "628" in social_ratio:
                        ratio_value = "1200x628"
                        
                    # Generate Pillow Share Card in memory
                    img_bytes = generate_share_card(trade_data_social, template=social_template, size_ratio=ratio_value)
                    
                    # Preview rendering
                    st.markdown("**Pratinjau Hasil Gambar:**")
                    if ratio_value == "1080x1920":
                        st.image(img_bytes, caption="Story Preview", width=260)
                    elif ratio_value == "1200x628":
                        st.image(img_bytes, caption="Telegram Preview", width=420)
                    else:
                        st.image(img_bytes, caption="Feed Square Preview", width=350)
                        
                with col_sc_act:
                    st.subheader("📤 Aksi & Pembagian Laporan")
                    
                    # Download button
                    st.download_button(
                        label="📥 Unduh Gambar Share Card (PNG)",
                        data=img_bytes,
                        file_name=f"SmartSaham_Exit_{trade_data_social['ticker'].split('.')[0]}_{ratio_value}.png",
                        mime="image/png",
                        use_container_width=True
                    )
                    
                    st.write("")
                    st.markdown("---")
                    st.write("🚀 **Kirim ke Telegram Channel / Group**")
                    
                    # Setup Auto-Caption
                    ticker_clean = trade_data_social['ticker'].split('.')[0]
                    roi_val = trade_data_social['return_percentage']
                    buy_val = trade_data_social['buy_price']
                    sell_val = trade_data_social['sell_price']
                    hold_days = trade_data_social['holding_days']
                    sig_buy = trade_data_social['app_signal_at_buy']
                    f_score = trade_data_social['final_score_at_buy']
                    tp1_h = "Yes" if trade_data_social.get('tp1_hit') else "No"
                    sl_h = "Yes" if trade_data_social.get('sl_hit') else "No"
                    exit_reason_text = trade_data_social.get('sell_reason', 'Manual Sell') if trade_data_social.get('sell_reason') else 'Manual Sell'
                    
                    clean_sig_buy = clean_signal_name(sig_buy)
                    if roi_val >= 0:
                        default_caption = f"""Trade Closed: {ticker_clean}
Result: +{roi_val:.2f}%
Entry Price: {buy_val:,.0f}
Exit Price: {sell_val:,.0f}
Holding: {hold_days} days
Signal at Screening: {clean_sig_buy}
Final Score: {f_score:.1f}
TP1 Hit: {tp1_h}
SL Hit: {sl_h}
Generated by Smart Saham Premium (AI Stock Screening & Risk Monitoring Platform).
For tracking & evaluation only. Not financial advice."""
                    else:
                        default_caption = f"""Trade Closed: {ticker_clean}
Result: {roi_val:.2f}%
Entry Price: {buy_val:,.0f}
Exit Price: {sell_val:,.0f}
Holding: {hold_days} days
Signal at Screening: {clean_sig_buy}
Final Score: {f_score:.1f}
Exit Reason: {exit_reason_text}
Generated by Smart Saham Premium (AI Stock Screening & Risk Monitoring Platform).
For tracking & evaluation only. Not financial advice."""
                        
                    custom_caption = st.text_area(
                        "Kustomisasi Pesan Caption (Bisa diedit/copas):",
                        value=default_caption,
                        height=230
                    )
                    
                    # Telegram credentials fetch
                    bot_token_social = tg_bot_token if tg_bot_token else os.environ.get("TELEGRAM_BOT_TOKEN", "")
                    chat_id_social = tg_chat_id if tg_chat_id else os.environ.get("TELEGRAM_CHAT_ID", "")
                    
                    if not bot_token_social or not chat_id_social:
                        st.warning("⚠️ Konfigurasi Telegram Bot belum lengkap di sidebar kiri (khusus admin 'fra') untuk mengirim langsung.")
                    else:
                        if st.button("📤 Kirim Foto + Caption ke Telegram", use_container_width=True):
                            with st.spinner("Mengirim gambar ke Telegram..."):
                                success, msg = send_telegram_photo(bot_token_social, chat_id_social, img_bytes, custom_caption)
                                if success:
                                    st.success(msg)
                                else:
                                    st.error(msg)
                                    
                    st.write("")
                    st.info("💡 **Tips Instagram Sharing**: Salin teks caption di atas, unduh gambar PNG di sebelah kiri, lalu unggah secara manual atau gunakan penjadwalan favorit Anda.")
        else:
            st.info("💡 Belum ada posisi portofolio yang terdaftar. Anda dapat mencatat transaksi pertama Anda di tab **💼 Portfolio & Accuracy**.")

    if is_admin:
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
    <h5 style="color: #f59e0b; margin: 0 0 5px 0; font-weight:700;">⚠️ DISCLAIMER & REGULATORY COMPLIANCE</h5>
    <p style="color: #cbd5e1; font-size: 0.85rem; margin: 0; line-height:1.4;">
        <b>Aplikasi ini bukan platform rekomendasi saham untuk beli/jual, melainkan AI stock screening & risk monitoring platform.</b> 
        Seluruh keputusan investasi atau transaksi di pasar modal adalah tanggung jawab pribadi pengguna secara penuh. Hasil screening, skor teknikal/flow, dan indikator yang ditampilkan 
        hanyalah hasil pemrosesan algoritma data historis dan bukan merupakan ajakan, perintah, atau saran finansial dari pihak pengembang atau OJK.
    </p>
</div>
""", unsafe_allow_html=True)
st.write("")
