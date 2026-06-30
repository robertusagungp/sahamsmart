import os
import pandas as pd
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

class AnalysisStorage:
    """
    Handles persistence of stock analysis logs, user management, and user activity logging.
    Supports CSV logging, SQLite, and PostgreSQL (e.g. Neon DB) with graceful fallbacks.
    """
    def __init__(self, db_url: Optional[str] = None, csv_path: str = "data/daily_analysis_log.csv", sqlite_path: str = "data/stock_analysis.db"):
        self.csv_path = csv_path
        self.sqlite_path = sqlite_path
        self.db_url = db_url or os.environ.get("DATABASE_URL")
        
        # User and Activity Log CSV fallbacks
        self.users_csv_path = "data/users.csv"
        self.activity_csv_path = "data/user_activity_log.csv"
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.csv_path) or '.', exist_ok=True)
        os.makedirs(os.path.dirname(self.sqlite_path) or '.', exist_ok=True)
        
        # Initialize SQL engine
        self.engine = None
        self._init_db()

    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def _init_db(self):
        """Initializes the database connection (PostgreSQL or SQLite)."""
        try:
            from sqlalchemy import create_engine
            
            # Choose database URL
            if self.db_url:
                actual_url = self.db_url
                if actual_url.startswith("postgres://"):
                    actual_url = actual_url.replace("postgres://", "postgresql://", 1)
                
                print("Connecting to Neon/PostgreSQL database...")
                self.engine = create_engine(actual_url, connect_args={"sslmode": "require"} if "localhost" not in actual_url else {})
            else:
                print(f"Connecting to local SQLite database: {self.sqlite_path}")
                self.engine = create_engine(f"sqlite:///{self.sqlite_path}")
            
            # Create tables if they don't exist
            self._create_tables_if_not_exists()
        except Exception as e:
            print(f"Warning: Failed to initialize SQL database: {str(e)}. Falling back to CSV-only operations.")
            self.engine = None

    def _create_tables_if_not_exists(self):
        if not self.engine:
            return
        try:
            from sqlalchemy import MetaData, Table, Column, Integer, Float, String, Date, DateTime
            metadata = MetaData()
            
            # 1. Stock Analysis Logs Table
            self.table_analysis = Table(
                'stock_analysis_logs', metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('tanggal', Date, nullable=False),
                Column('ticker', String(20), nullable=False),
                Column('close_price', Float, nullable=False),
                Column('rsi', Float, nullable=True),
                Column('ma20', Float, nullable=True),
                Column('ma50', Float, nullable=True),
                Column('momentum_1m', Float, nullable=True),
                Column('momentum_3m', Float, nullable=True),
                Column('volume_ratio', Float, nullable=True),
                Column('score', Integer, nullable=False),
                Column('recommendation', String(10), nullable=False)
            )
            
            # 2. Users Table for Authentication
            self.table_users = Table(
                'users', metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('username', String(50), nullable=False, unique=True),
                Column('password_hash', String(100), nullable=False),
                Column('email', String(100), nullable=True),
                Column('created_at', DateTime, default=datetime.utcnow)
            )
            
            # 3. User Activity Logs Table
            self.table_activities = Table(
                'user_activity_logs', metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('username', String(50), nullable=False),
                Column('action', String(100), nullable=False),
                Column('ticker', String(20), nullable=True),
                Column('timestamp', DateTime, default=datetime.utcnow)
            )
            
            metadata.create_all(self.engine)
            print("Database tables initialized successfully.")
        except Exception as e:
            print(f"Error creating database tables: {str(e)}")
            self.engine = None

    # ================= USER AUTHENTICATION MODULE =================

    def create_user(self, username: str, password: str, email: str = "") -> Dict[str, Any]:
        """
        Registers a new user. Returns a dict with 'success' and 'message'.
        """
        username = username.strip().lower()
        if not username or not password:
            return {"success": False, "message": "Username dan password tidak boleh kosong."}
            
        password_hash = self._hash_password(password)
        created_at = datetime.utcnow()
        
        # 1. SQL Database Register
        if self.engine:
            try:
                from sqlalchemy import text
                # Check if username exists
                with self.engine.begin() as conn:
                    result = conn.execute(
                        text("SELECT id FROM users WHERE LOWER(username) = :u"),
                        {"u": username}
                    ).fetchone()
                    if result:
                        return {"success": False, "message": "Username sudah terdaftar."}
                        
                    # Insert user
                    conn.execute(
                        text("INSERT INTO users (username, password_hash, email, created_at) VALUES (:u, :p, :e, :c)"),
                        {"u": username, "p": password_hash, "e": email, "c": created_at}
                    )
                return {"success": True, "message": "Registrasi berhasil! Silakan login."}
            except Exception as e:
                print(f"Error creating user in DB: {str(e)}")
                # Fail over to CSV
                
        # 2. CSV Register Fallback
        try:
            if os.path.exists(self.users_csv_path):
                df_users = pd.read_csv(self.users_csv_path)
                # Check duplicate
                if not df_users.empty and username in df_users['username'].astype(str).str.lower().values:
                    return {"success": False, "message": "Username sudah terdaftar."}
            else:
                df_users = pd.DataFrame(columns=['username', 'password_hash', 'email', 'created_at'])
                
            new_user = pd.DataFrame([{
                'username': username,
                'password_hash': password_hash,
                'email': email,
                'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S')
            }])
            df_users = pd.concat([df_users, new_user], ignore_index=True)
            df_users.to_csv(self.users_csv_path, index=False)
            return {"success": True, "message": "Registrasi berhasil (Lokal CSV)! Silakan login."}
        except Exception as e:
            return {"success": False, "message": f"Registrasi gagal: {str(e)}"}

    def authenticate_user(self, username: str, password: str) -> bool:
        """
        Authenticates username and password. Returns True if match, False otherwise.
        """
        username = username.strip().lower()
        password_hash = self._hash_password(password)
        
        # 1. SQL Database Auth
        if self.engine:
            try:
                from sqlalchemy import text
                with self.engine.connect() as conn:
                    result = conn.execute(
                        text("SELECT password_hash FROM users WHERE LOWER(username) = :u"),
                        {"u": username}
                    ).fetchone()
                    if result and result[0] == password_hash:
                        return True
            except Exception as e:
                print(f"Database Auth failed: {str(e)}")
                
        # 2. CSV Auth Fallback
        if os.path.exists(self.users_csv_path):
            try:
                df_users = pd.read_csv(self.users_csv_path)
                if not df_users.empty:
                    match = df_users[
                        (df_users['username'].astype(str).str.lower() == username) & 
                        (df_users['password_hash'] == password_hash)
                    ]
                    return len(match) > 0
            except Exception as e:
                print(f"CSV Auth error: {str(e)}")
                
        return False

    # ================= USER ACTIVITY LOGGING MODULE =================

    def log_activity(self, username: str, action: str, ticker: Optional[str] = None) -> bool:
        """
        Logs a user action (e.g. view details, run screener, login) to DB and CSV.
        """
        username = username.strip().lower()
        now = datetime.utcnow()
        
        success_db = False
        success_csv = False
        
        # 1. DB Log
        if self.engine:
            try:
                from sqlalchemy import text
                with self.engine.begin() as conn:
                    conn.execute(
                        text("INSERT INTO user_activity_logs (username, action, ticker, timestamp) VALUES (:u, :a, :t, :time)"),
                        {"u": username, "a": action, "t": ticker, "time": now}
                    )
                success_db = True
            except Exception as e:
                print(f"Error logging activity to DB: {str(e)}")
                
        # 2. CSV Log Fallback
        try:
            log_entry = pd.DataFrame([{
                'username': username,
                'action': action,
                'ticker': ticker or "",
                'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')
            }])
            if os.path.exists(self.activity_csv_path):
                log_entry.to_csv(self.activity_csv_path, mode='a', header=False, index=False)
            else:
                log_entry.to_csv(self.activity_csv_path, index=False)
            success_csv = True
        except Exception as e:
            print(f"Error logging activity to CSV: {str(e)}")
            
        return success_db or success_csv

    def load_activity_logs(self, limit: int = 200) -> pd.DataFrame:
        """
        Load user activity logs for presentation.
        """
        if self.engine:
            try:
                query = f"SELECT username, action, ticker, timestamp FROM user_activity_logs ORDER BY timestamp DESC LIMIT {limit}"
                return pd.read_sql(query, con=self.engine)
            except Exception as e:
                print(f"Failed to query activities from DB: {str(e)}")
                
        if os.path.exists(self.activity_csv_path):
            try:
                df = pd.read_csv(self.activity_csv_path)
                df = df.sort_values(by='timestamp', ascending=False)
                return df.head(limit)
            except Exception as e:
                print(f"Failed to read activity CSV: {str(e)}")
                
        return pd.DataFrame()

    # ================= STOCK ANALYSIS RECORD LOGGING =================

    def save_analysis(self, records: List[Dict[str, Any]]) -> bool:
        """
        Save daily stock analysis records to Database and CSV.
        """
        if not records:
            return False
            
        success_db = False
        success_csv = False
        
        # Prepare data
        df = pd.DataFrame(records)
        required_cols = [
            'tanggal', 'ticker', 'close_price', 'rsi', 'ma20', 'ma50', 
            'momentum_1m', 'momentum_3m', 'volume_ratio', 'score', 'recommendation'
        ]
        
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        df = df[required_cols].copy()
        df['tanggal'] = pd.to_datetime(df['tanggal']).dt.date
        
        # 1. SQL DB
        if self.engine:
            try:
                df.to_sql('stock_analysis_logs', con=self.engine, if_exists='append', index=False)
                success_db = True
            except Exception as e:
                print(f"Error saving to database: {str(e)}")
        
        # 2. CSV Log
        try:
            csv_df = df.copy()
            csv_df['tanggal'] = csv_df['tanggal'].apply(lambda x: x.strftime('%Y-%m-%d') if hasattr(x, 'strftime') else str(x))
            
            if os.path.exists(self.csv_path):
                existing_df = pd.read_csv(self.csv_path)
                combined = pd.concat([existing_df, csv_df], ignore_index=True)
                combined = combined.drop_duplicates(subset=['tanggal', 'ticker'], keep='last')
                combined.to_csv(self.csv_path, index=False)
            else:
                csv_df.to_csv(self.csv_path, index=False)
            success_csv = True
        except Exception as e:
            print(f"Error saving to CSV: {str(e)}")
            
        return success_db or success_csv

    def load_historical_logs(self, limit: int = 500) -> pd.DataFrame:
        """
        Load historical analysis logs.
        """
        if self.engine:
            try:
                query = f"SELECT tanggal, ticker, close_price, rsi, ma20, ma50, momentum_1m, momentum_3m, volume_ratio, score, recommendation FROM stock_analysis_logs ORDER BY tanggal DESC, score DESC LIMIT {limit}"
                df = pd.read_sql(query, con=self.engine)
                return df
            except Exception as e:
                print(f"Failed to query database: {str(e)}")
                
        if os.path.exists(self.csv_path):
            try:
                df = pd.read_csv(self.csv_path)
                df = df.sort_values(by=['tanggal', 'score'], ascending=[False, False])
                return df.head(limit)
            except Exception as e:
                print(f"Failed to read CSV: {str(e)}")
                
        return pd.DataFrame()
