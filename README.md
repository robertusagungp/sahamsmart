# 📈 Smart Saham - Prototype Rekomendasi Saham Indonesia

Aplikasi dashboard prototype berbasis web menggunakan **Streamlit** untuk melakukan screening dan rekomendasi saham Indonesia secara modular, aman, dan siap dideploy ke cloud (seperti Streamlit Cloud dengan Neon DB PostgreSQL).

Aplikasi ini mengambil data historis dari Yahoo Finance (`yfinance`), menghitung indikator teknikal & volume, melakukan penilaian skor terstandarisasi, dan menyimpannya dalam database relasional.

---

## 🛠️ Fitur Utama
1. **Interactive Dashboard**: Visualisasi ringkasan rekomendasi (BUY / WATCH / AVOID) dan ranking saham berdasar skor tertinggi.
2. **Technical Indicators**: Perhitungan MA20, MA50, RSI 14, Volume Ratio vs MA20, serta Momentum Harga 1 Bulan & 3 Bulan secara real-time.
3. **Interactive Charts**: Grafis historis harga saham dengan overlay MA20 & MA50, serta indikator RSI lengkap dengan garis batas ambang batas (threshold).
4. **Cloud-Ready Logging System**: Secara otomatis menyimpan histori analisis harian ke **PostgreSQL (Neon DB)** atau lokal fallback ke **SQLite** dan file **CSV**.
5. **Detail & Risiko**: Analisis granular per saham mengenai poin positif teknikal beserta catatan risiko teknikal (seperti overbought, trend melemah, volume sepi).

---

## 🚀 Cara Menjalankan Aplikasi

### 1. Prasyarat (Prerequisites)
Pastikan Anda telah menginstal **Python 3.8** atau versi di atasnya di komputer Anda.

### 2. Instalasi Dependensi
Buka terminal/command prompt di folder project ini dan jalankan perintah berikut:
```bash
pip install -r requirements.txt
```

### 3. Jalankan Aplikasi
Jalankan aplikasi Streamlit dengan perintah berikut:
```bash
streamlit run app.py
```
Aplikasi akan otomatis terbuka di browser Anda pada alamat `http://localhost:8501`.

---

## ☁️ Deployment ke Streamlit Cloud & Neon DB

Aplikasi ini dirancang untuk dapat dengan mudah dideploy ke **Streamlit Community Cloud** dengan basis data cloud **Neon DB** (PostgreSQL).

### Langkah Menghubungkan Neon DB:
1. Buat database baru di akun [Neon.tech](https://neon.tech/).
2. Salin *Connection String* PostgreSQL yang disediakan (biasanya berformat `postgres://user:password@hostname/dbname?sslmode=require`).
3. Pada halaman dashboard Streamlit Cloud Anda:
   * Masuk ke **Settings** > **Secrets**.
   * Tambahkan konfigurasi `DATABASE_URL` seperti berikut:
     ```toml
     DATABASE_URL = "postgres://user:password@hostname/dbname?sslmode=require"
     ```
4. Aplikasi akan otomatis mendeteksi konfigurasi tersebut dan menyimpan hasil analisis ke database Neon DB Anda setiap kali analisis dijalankan.
5. Jika tidak ada `DATABASE_URL` yang dideklarasikan, aplikasi akan secara aman beralih menggunakan basis data lokal SQLite (`data/stock_analysis.db`) dan CSV (`data/daily_analysis_log.csv`).

---

## 📊 Penjelasan Logika Scoring

Penilaian/scoring saham menggunakan basis awal **50 poin**, yang kemudian dimodifikasi berdasarkan indikator teknikal sebagai berikut:

| Kondisi Indikator | Aksi Skor | Alasan / Keterangan |
| :--- | :--- | :--- |
| **Harga Close > MA20** | `+10` | Tren harga jangka pendek positif |
| **Harga Close > MA50** | `+10` | Tren harga jangka menengah positif |
| **MA20 > MA50** | `+10` | Terjadi Golden Cross (Konfirmasi tren naik) |
| **RSI antara 40 dan 70** | `+10` | Indikator kekuatan harga berada di area sehat/netral |
| **RSI > 75** | `-15` | Indikator Overbought (Rawan jenuh beli / profit taking) |
| **Momentum 1 Bulan Positif** | `+10` | Pergerakan harga 1 bulan terakhir naik |
| **Momentum 3 Bulan Positif** | `+10` | Pergerakan harga 3 bulan terakhir naik |
| **Volume Hari Terakhir > Rata-rata 20 Hari** | `+5` | Partisipasi pasar meningkat saat transaksi terakhir |

### Batasan Nilai Skor:
* Nilai skor dibatasi minimal **0** dan maksimal **100**.
* **Klasifikasi Rekomendasi:**
  * **Skor 75 – 100:** 🟢 **BUY**
  * **Skor 50 – 74:** 🟡 **WATCH**
  * **Skor < 50:** 🔴 **AVOID**

---

## 📁 Struktur Folder Project
```text
├── app.py                     # Entry point dashboard utama Streamlit
├── requirements.txt           # Daftar library Python yang dibutuhkan
├── README.md                  # Dokumentasi panduan aplikasi
├── src/
│   ├── data_loader.py         # Modul untuk fetching data saham (yfinance)
│   ├── indicators.py          # Modul perhitungan teknikal (MA, RSI, Volume, Momentum)
│   ├── scoring.py             # Modul kalkulasi bobot poin & rekomendasi
│   └── storage.py             # Modul logging analisis ke Neon DB / SQLite / CSV
└── data/                      # Folder penyimpanan lokal (di-generate otomatis)
    ├── stock_analysis.db      # Database SQLite lokal (fallback)
    └── daily_analysis_log.csv # Log CSV lokal (fallback & cadangan)
```

---

## ⚠️ Catatan Keterbatasan Data & Disclaimer

### Keterbatasan Data
* **Delayed / EOD Data**: Data yang diambil dari `yfinance` untuk pasar Indonesia (`.JK`) memiliki jeda (delay) sekitar 15 menit dari pasar live (real-time) dan terkadang bergantung pada stabilitas server Yahoo Finance.
* **Production Options**: Untuk penggunaan tingkat produksi (production-ready), disarankan mengganti modul `src/data_loader.py` dengan data feed berlisensi resmi, seperti API resmi IDX, Bloomberg, Refinitiv, atau vendor data lokal terpercaya.

### Disclaimer
> [!IMPORTANT]
> **Hasil analisis dan rekomendasi yang dihasilkan oleh aplikasi ini murni untuk kebutuhan analisis awal, dan bukan merupakan ajakan membeli atau menjual saham (bukan financial advice final).** 
> Keputusan investasi sepenuhnya di tangan pengguna. Pengguna wajib menyandingkan hasil skrining ini dengan analisis fundamental, berita makroekonomi, dan analisis risiko personal secara komprehensif sebelum bertransaksi di bursa.
