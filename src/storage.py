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
                Column('created_at', DateTime, default=datetime.utcnow),
                Column('plan', String(30), default='Smart Saham All Access'),
                Column('active_mode', String(50), default='Swing Trading Mode'),
                Column('role', String(20), default='customer')
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
            
            # 4. User Watchlist Table
            self.table_watchlist = Table(
                'user_watchlist', metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('username', String(50), nullable=False),
                Column('ticker', String(20), nullable=False),
                Column('added_date', Date, nullable=False),
                Column('app_signal_when_added', String(20), nullable=True),
                Column('final_score_when_added', Float, nullable=True),
                Column('notes', String(255), nullable=True),
                Column('status', String(20), default="Watch Only")
            )
            
            # 5. Real Trades Table
            self.table_real_trades = Table(
                'real_trades', metadata,
                Column('trade_id', Integer, primary_key=True, autoincrement=True),
                Column('username', String(50), nullable=False),
                Column('ticker', String(20), nullable=False),
                Column('buy_date', Date, nullable=False),
                Column('buy_price', Float, nullable=False),
                Column('lot_quantity', Integer, nullable=False),
                Column('total_value', Float, nullable=False),
                Column('app_signal_at_buy', String(20), nullable=True),
                Column('technical_score_at_buy', Float, nullable=True),
                Column('flow_score_at_buy', Float, nullable=True),
                Column('final_score_at_buy', Float, nullable=True),
                Column('entry_area_at_buy', String(50), nullable=True),
                Column('tp1_at_buy', Float, nullable=True),
                Column('tp2_at_buy', Float, nullable=True),
                Column('sl_at_buy', Float, nullable=True),
                Column('reason_at_buy', String(255), nullable=True),
                Column('risk_note_at_buy', String(255), nullable=True),
                Column('sell_date', Date, nullable=True),
                Column('sell_price', Float, nullable=True),
                Column('sell_reason', String(255), nullable=True),
                Column('exit_type', String(50), nullable=True),
                Column('status', String(20), default="Open Position"),
                Column('user_notes', String(255), nullable=True),
                Column('created_at', DateTime, default=datetime.utcnow),
                Column('updated_at', DateTime, default=datetime.utcnow),
                Column('analysis_mode', String(30), default="Swing")
            )
            
            # 6. Trade Evaluation Table
            self.table_trade_evaluation = Table(
                'trade_evaluation', metadata,
                Column('evaluation_id', Integer, primary_key=True, autoincrement=True),
                Column('trade_id', Integer, nullable=False, unique=True),
                Column('ticker', String(20), nullable=False),
                Column('current_price', Float, nullable=True),
                Column('realized_profit_loss', Float, nullable=True),
                Column('unrealized_profit_loss', Float, nullable=True),
                Column('return_percentage', Float, nullable=True),
                Column('holding_days', Integer, nullable=True),
                Column('tp1_hit', Integer, default=0),
                Column('tp1_hit_date', Date, nullable=True),
                Column('tp2_hit', Integer, default=0),
                Column('tp2_hit_date', Date, nullable=True),
                Column('sl_hit', Integer, default=0),
                Column('sl_hit_date', Date, nullable=True),
                Column('max_gain_after_buy', Float, nullable=True),
                Column('max_drawdown_after_buy', Float, nullable=True),
                Column('prediction_result', String(50), nullable=True),
                Column('prediction_result_detail', String(255), nullable=True),
                Column('evaluated_at', DateTime, default=datetime.utcnow)
            )
            
            metadata.create_all(self.engine)
            
            # Self-healing migration for existing databases
            try:
                from sqlalchemy import text
                with self.engine.begin() as conn:
                    conn.execute(text("SELECT analysis_mode FROM real_trades LIMIT 1"))
            except Exception:
                try:
                    from sqlalchemy import text
                    with self.engine.begin() as conn:
                        conn.execute(text("ALTER TABLE real_trades ADD COLUMN analysis_mode VARCHAR(30) DEFAULT 'Swing'"))
                        print("Migration: analysis_mode column successfully added to real_trades table.")
                except Exception as ex:
                    print(f"Migration warning: {ex}")
                    
            # Self-healing migration for users table plan, active_mode, and role
            try:
                from sqlalchemy import text
                with self.engine.begin() as conn:
                    conn.execute(text("SELECT role FROM users LIMIT 1"))
            except Exception:
                try:
                    from sqlalchemy import text
                    with self.engine.begin() as conn:
                        # Attempt to add columns one by one to prevent migration crashes
                        try:
                            conn.execute(text("ALTER TABLE users ADD COLUMN plan VARCHAR(30) DEFAULT 'Smart Saham All Access'"))
                        except Exception:
                            pass
                        try:
                            conn.execute(text("ALTER TABLE users ADD COLUMN active_mode VARCHAR(50) DEFAULT 'Swing Trading Mode'"))
                        except Exception:
                            pass
                        try:
                            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'customer'"))
                        except Exception:
                            pass
                        print("Migration: users table columns updated successfully.")
                except Exception as ex:
                    print(f"Migration warning for users table columns: {ex}")

            # Run persistent data migration (update admin roles and convert plan values)
            try:
                from sqlalchemy import text
                with self.engine.begin() as conn:
                    conn.execute(text("UPDATE users SET role = 'admin' WHERE LOWER(username) = 'fra'"))
                    conn.execute(text("UPDATE users SET plan = 'Smart Saham All Access' WHERE plan = 'All Mode' OR plan = 'All Mode Plan'"))
                    conn.execute(text("UPDATE users SET plan = 'Smart Saham Focus Mode' WHERE plan = '1 Mode' OR plan = '1 Mode Plan'"))
                    conn.execute(text("UPDATE users SET plan = 'Smart Saham Radar Free' WHERE plan = 'Free' OR plan = 'Free Plan'"))
            except Exception as ex:
                print(f"Data migration warning: {ex}")
                    
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
                        text("INSERT INTO users (username, password_hash, email, created_at, plan, active_mode) VALUES (:u, :p, :e, :c, 'All Mode', 'Swing Trading Mode')"),
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
                df_users = pd.DataFrame(columns=['username', 'password_hash', 'email', 'created_at', 'plan', 'active_mode'])
                
            new_user = pd.DataFrame([{
                'username': username,
                'password_hash': password_hash,
                'email': email,
                'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'plan': 'All Mode',
                'active_mode': 'Swing Trading Mode'
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

    def get_user_profile(self, username: str) -> Dict[str, Any]:
        """
        Retrieves user plan, active_mode, and role.
        """
        username = username.strip().lower()
        # Default fallback
        profile = {
            "plan": "Smart Saham All Access", 
            "active_mode": "Swing Trading Mode", 
            "role": "admin" if username == "fra" else "customer"
        }
        
        # 1. SQL Database Fetch
        if self.engine:
            try:
                from sqlalchemy import text
                with self.engine.connect() as conn:
                    result = conn.execute(
                        text("SELECT plan, active_mode, role FROM users WHERE LOWER(username) = :u"),
                        {"u": username}
                    ).fetchone()
                    if result:
                        profile["plan"] = result[0] or "Smart Saham All Access"
                        profile["active_mode"] = result[1] or "Swing Trading Mode"
                        profile["role"] = result[2] or ("admin" if username == "fra" else "customer")
            except Exception as e:
                print(f"Error fetching user profile from DB: {str(e)}")
                
        # 2. CSV Fetch Fallback
        elif os.path.exists(self.users_csv_path):
            try:
                df_users = pd.read_csv(self.users_csv_path)
                if not df_users.empty:
                    # check if cols exist
                    if 'plan' not in df_users.columns:
                        df_users['plan'] = 'Smart Saham All Access'
                    if 'active_mode' not in df_users.columns:
                        df_users['active_mode'] = 'Swing Trading Mode'
                    if 'role' not in df_users.columns:
                        df_users['role'] = 'customer'
                    
                    match = df_users[df_users['username'].astype(str).str.lower() == username]
                    if not match.empty:
                        profile["plan"] = match.iloc[0].get("plan", "Smart Saham All Access")
                        profile["active_mode"] = match.iloc[0].get("active_mode", "Swing Trading Mode")
                        profile["role"] = match.iloc[0].get("role", "admin" if username == "fra" else "customer")
            except Exception as e:
                print(f"CSV profile fetch error: {str(e)}")
                
        # Normalization of old names on the fly
        plan_map = {
            "All Mode": "Smart Saham All Access",
            "All Mode Plan": "Smart Saham All Access",
            "1 Mode": "Smart Saham Focus Mode",
            "1 Mode Plan": "Smart Saham Focus Mode",
            "Free": "Smart Saham Radar Free",
            "Free Plan": "Smart Saham Radar Free"
        }
        profile["plan"] = plan_map.get(profile["plan"], profile["plan"])
        return profile

    def update_user_profile(self, username: str, plan: str, active_mode: str, role: Optional[str] = None) -> bool:
        """
        Updates user plan, active_mode, and role in DB and CSV.
        """
        username = username.strip().lower()
        if role is None:
            role = "admin" if username == "fra" else "customer"
            
        success_db = False
        success_csv = False
        
        # 1. SQL Database Update
        if self.engine:
            try:
                from sqlalchemy import text
                with self.engine.begin() as conn:
                    conn.execute(
                        text("UPDATE users SET plan = :plan, active_mode = :mode, role = :role WHERE LOWER(username) = :u"),
                        {"plan": plan, "mode": active_mode, "role": role, "u": username}
                    )
                success_db = True
            except Exception as e:
                print(f"Error updating user profile in DB: {str(e)}")
                
        # 2. CSV Update Fallback
        if os.path.exists(self.users_csv_path):
            try:
                df_users = pd.read_csv(self.users_csv_path)
                if not df_users.empty:
                    if 'plan' not in df_users.columns:
                        df_users['plan'] = 'Smart Saham All Access'
                    if 'active_mode' not in df_users.columns:
                        df_users['active_mode'] = 'Swing Trading Mode'
                    if 'role' not in df_users.columns:
                        df_users['role'] = 'customer'
                        
                    # Find index
                    idx = df_users[df_users['username'].astype(str).str.lower() == username].index
                    if not idx.empty:
                        df_users.loc[idx, 'plan'] = plan
                        df_users.loc[idx, 'active_mode'] = active_mode
                        df_users.loc[idx, 'role'] = role
                        df_users.to_csv(self.users_csv_path, index=False)
                        success_csv = True
            except Exception as e:
                print(f"CSV profile update error: {str(e)}")
                
        return success_db or success_csv

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

    # ================= WATCHLIST OPERATIONS =================

    def add_to_watchlist(self, username: str, ticker: str, signal: str, score: float, notes: str = "") -> bool:
        if not self.engine:
            return False
        try:
            from sqlalchemy import text
            from datetime import date
            with self.engine.begin() as conn:
                # Check if already exists in watchlist
                exists = conn.conn.execute(
                    text("SELECT id FROM user_watchlist WHERE LOWER(username) = :u AND UPPER(ticker) = :t"),
                    {"u": username.lower(), "t": ticker.upper()}
                ).fetchone() if hasattr(conn, "conn") else conn.execute(
                    text("SELECT id FROM user_watchlist WHERE LOWER(username) = :u AND UPPER(ticker) = :t"),
                    {"u": username.lower(), "t": ticker.upper()}
                ).fetchone()
                
                if exists:
                    # Update status
                    if hasattr(conn, "conn"):
                        conn.conn.execute(
                            text("UPDATE user_watchlist SET status = 'Watch Only', added_date = :d, app_signal_when_added = :s, final_score_when_added = :sc, notes = :n WHERE id = :id"),
                            {"d": date.today(), "s": signal, "sc": score, "n": notes, "id": exists[0]}
                        )
                    else:
                        conn.execute(
                            text("UPDATE user_watchlist SET status = 'Watch Only', added_date = :d, app_signal_when_added = :s, final_score_when_added = :sc, notes = :n WHERE id = :id"),
                            {"d": date.today(), "s": signal, "sc": score, "n": notes, "id": exists[0]}
                        )
                else:
                    # Insert new
                    if hasattr(conn, "conn"):
                        conn.conn.execute(
                            text("INSERT INTO user_watchlist (username, ticker, added_date, app_signal_when_added, final_score_when_added, notes, status) VALUES (:u, :t, :d, :s, :sc, :n, 'Watch Only')"),
                            {"u": username.lower(), "t": ticker.upper(), "d": date.today(), "s": signal, "sc": score, "n": notes}
                        )
                    else:
                        conn.execute(
                            text("INSERT INTO user_watchlist (username, ticker, added_date, app_signal_when_added, final_score_when_added, notes, status) VALUES (:u, :t, :d, :s, :sc, :n, 'Watch Only')"),
                            {"u": username.lower(), "t": ticker.upper(), "d": date.today(), "s": signal, "sc": score, "n": notes}
                        )
            return True
        except Exception as e:
            print(f"Error adding to watchlist: {str(e)}")
            return False

    def get_watchlist(self, username: str) -> pd.DataFrame:
        if not self.engine:
            return pd.DataFrame()
        try:
            query = f"SELECT id, ticker, added_date, app_signal_when_added, final_score_when_added, notes, status FROM user_watchlist WHERE LOWER(username) = '{username.lower()}' AND status = 'Watch Only'"
            return pd.read_sql(query, con=self.engine)
        except Exception as e:
            print(f"Error fetching watchlist: {str(e)}")
            return pd.DataFrame()

    def remove_from_watchlist(self, username: str, ticker: str) -> bool:
        if not self.engine:
            return False
        try:
            from sqlalchemy import text
            with self.engine.begin() as conn:
                if hasattr(conn, "conn"):
                    conn.conn.execute(
                        text("DELETE FROM user_watchlist WHERE LOWER(username) = :u AND UPPER(ticker) = :t"),
                        {"u": username.lower(), "t": ticker.upper()}
                    )
                else:
                    conn.execute(
                        text("DELETE FROM user_watchlist WHERE LOWER(username) = :u AND UPPER(ticker) = :t"),
                        {"u": username.lower(), "t": ticker.upper()}
                    )
            return True
        except Exception as e:
            print(f"Error removing from watchlist: {str(e)}")
            return False

    # ================= REAL TRADES & EVALUATIONS OPERATIONS =================

    def add_real_trade(self, username: str, ticker: str, buy_date: Any, buy_price: float, lot_quantity: int, score_data: Dict[str, Any], user_notes: str = "", analysis_mode: str = "Swing") -> bool:
        if not self.engine:
            return False
        try:
            from sqlalchemy import text
            total_value = buy_price * lot_quantity * 100 # 1 lot = 100 shares in Indonesia
            
            with self.engine.begin() as conn:
                query_str = """
                    INSERT INTO real_trades (
                        username, ticker, buy_date, buy_price, lot_quantity, total_value,
                        app_signal_at_buy, technical_score_at_buy, flow_score_at_buy, final_score_at_buy,
                        entry_area_at_buy, tp1_at_buy, tp2_at_buy, sl_at_buy, reason_at_buy, risk_note_at_buy,
                        status, user_notes, created_at, updated_at, analysis_mode
                    ) VALUES (
                        :username, :ticker, :buy_date, :buy_price, :lot_quantity, :total_value,
                        :app_signal, :tech_score, :flow_score, :final_score,
                        :entry_area, :tp1, :tp2, :sl, :reason, :risk_note,
                        'Open Position', :user_notes, :now, :now, :analysis_mode
                    )
                """
                params = {
                    "username": username.lower(),
                    "ticker": ticker.upper(),
                    "buy_date": buy_date,
                    "buy_price": buy_price,
                    "lot_quantity": lot_quantity,
                    "total_value": total_value,
                    "app_signal": score_data.get("recommendation", "Watchlist Prioritas"),
                    "tech_score": score_data.get("technical_score", 0) if score_data.get("technical_score") is not None else score_data.get("score", 0),
                    "flow_score": score_data.get("flow_score", 0) if score_data.get("flow_score") is not None else score_data.get("score", 0),
                    "final_score": score_data.get("final_score", score_data.get("score", 0)),
                    "entry_area": score_data.get("entry_area", ""),
                    "tp1": float(score_data.get("tp1", 0)) if isinstance(score_data.get("tp1"), (int, float)) else 0.0,
                    "tp2": float(score_data.get("tp2", 0)) if isinstance(score_data.get("tp2"), (int, float)) else 0.0,
                    "sl": float(score_data.get("sl", 0)) if isinstance(score_data.get("sl"), (int, float)) else 0.0,
                    "reason": score_data.get("entry_reason", "") if score_data.get("entry_reason") else (score_data.get("reasons")[0] if score_data.get("reasons") else ""),
                    "risk_note": "; ".join([r.replace("[Teknikal] ", "").replace("[Flow] ", "").replace("[Sinyal] ", "").replace("[Investasi] ", "").replace("[Scalping] ", "") for r in score_data.get("risks", []) if "Tidak ada" not in r][:2]),
                    "user_notes": user_notes,
                    "now": datetime.utcnow(),
                    "analysis_mode": analysis_mode
                }
                if hasattr(conn, "conn"):
                    conn.conn.execute(text(query_str), params)
                else:
                    conn.execute(text(query_str), params)
            return True
        except Exception as e:
            print(f"Error adding real trade: {str(e)}")
            return False

    def sell_real_trade(self, trade_id: int, sell_date: Any, sell_price: float, sell_reason: str, exit_type: str) -> bool:
        if not self.engine:
            return False
        try:
            from sqlalchemy import text
            with self.engine.begin() as conn:
                query_str = """
                    UPDATE real_trades 
                    SET sell_date = :sell_date, sell_price = :sell_price, 
                        sell_reason = :sell_reason, exit_type = :exit_type, 
                        status = 'Closed Position', updated_at = :now
                    WHERE trade_id = :trade_id
                """
                params = {
                    "trade_id": trade_id,
                    "sell_date": sell_date,
                    "sell_price": sell_price,
                    "sell_reason": sell_reason,
                    "exit_type": exit_type,
                    "now": datetime.utcnow()
                }
                if hasattr(conn, "conn"):
                    conn.conn.execute(text(query_str), params)
                else:
                    conn.execute(text(query_str), params)
            return True
        except Exception as e:
            print(f"Error selling real trade: {str(e)}")
            return False

    def get_real_trades(self, username: str) -> pd.DataFrame:
        if not self.engine:
            return pd.DataFrame()
        try:
            query = f"SELECT * FROM real_trades WHERE LOWER(username) = '{username.lower()}'"
            return pd.read_sql(query, con=self.engine)
        except Exception as e:
            print(f"Error fetching real trades: {str(e)}")
            return pd.DataFrame()

    def get_trade_evaluations(self, username: str) -> pd.DataFrame:
        if not self.engine:
            return pd.DataFrame()
        try:
            query = f"""
                SELECT t.*, e.current_price, e.realized_profit_loss, e.unrealized_profit_loss, 
                       e.return_percentage, e.holding_days, e.tp1_hit, e.tp1_hit_date, 
                       e.tp2_hit, e.tp2_hit_date, e.sl_hit, e.sl_hit_date, 
                       e.max_gain_after_buy, e.max_drawdown_after_buy, 
                       e.prediction_result, e.prediction_result_detail, e.evaluated_at
                FROM real_trades t
                LEFT JOIN trade_evaluation e ON t.trade_id = e.trade_id
                WHERE LOWER(t.username) = '{username.lower()}'
            """
            return pd.read_sql(query, con=self.engine)
        except Exception as e:
            print(f"Error fetching trade evaluations: {str(e)}")
            return pd.DataFrame()

    def save_or_update_evaluation(self, eval_data: Dict[str, Any]) -> bool:
        if not self.engine:
            return False
        try:
            from sqlalchemy import text
            trade_id = eval_data["trade_id"]
            
            with self.engine.begin() as conn:
                # Check if exists
                exists_query = text("SELECT evaluation_id FROM trade_evaluation WHERE trade_id = :tid")
                exists = conn.conn.execute(exists_query, {"tid": trade_id}).fetchone() if hasattr(conn, "conn") else conn.execute(exists_query, {"tid": trade_id}).fetchone()
                
                params = {
                    "tid": trade_id,
                    "ticker": eval_data["ticker"],
                    "curr_price": eval_data.get("current_price"),
                    "real_pl": eval_data.get("realized_profit_loss"),
                    "unreal_pl": eval_data.get("unrealized_profit_loss"),
                    "ret_pct": eval_data.get("return_percentage"),
                    "hold_days": eval_data.get("holding_days"),
                    "tp1_hit": 1 if eval_data.get("tp1_hit") else 0,
                    "tp1_date": eval_data.get("tp1_hit_date"),
                    "tp2_hit": 1 if eval_data.get("tp2_hit") else 0,
                    "tp2_date": eval_data.get("tp2_hit_date"),
                    "sl_hit": 1 if eval_data.get("sl_hit") else 0,
                    "sl_date": eval_data.get("sl_hit_date"),
                    "max_gain": eval_data.get("max_gain_after_buy"),
                    "max_dd": eval_data.get("max_drawdown_after_buy"),
                    "pred_res": eval_data.get("prediction_result"),
                    "pred_res_det": eval_data.get("prediction_result_detail"),
                    "now": datetime.utcnow()
                }
                
                if exists:
                    update_str = """
                        UPDATE trade_evaluation 
                        SET current_price = :curr_price, realized_profit_loss = :real_pl,
                            unrealized_profit_loss = :unreal_pl, return_percentage = :ret_pct,
                            holding_days = :hold_days, tp1_hit = :tp1_hit, tp1_hit_date = :tp1_date,
                            tp2_hit = :tp2_hit, tp2_hit_date = :tp2_date, sl_hit = :sl_hit, sl_hit_date = :sl_date,
                            max_gain_after_buy = :max_gain, max_drawdown_after_buy = :max_dd,
                            prediction_result = :pred_res, prediction_result_detail = :pred_res_det,
                            evaluated_at = :now
                        WHERE trade_id = :tid
                    """
                    if hasattr(conn, "conn"):
                        conn.conn.execute(text(update_str), params)
                    else:
                        conn.execute(text(update_str), params)
                else:
                    insert_str = """
                        INSERT INTO trade_evaluation (
                            trade_id, ticker, current_price, realized_profit_loss, unrealized_profit_loss,
                            return_percentage, holding_days, tp1_hit, tp1_hit_date, tp2_hit, tp2_hit_date,
                            sl_hit, sl_hit_date, max_gain_after_buy, max_drawdown_after_buy,
                            prediction_result, prediction_result_detail, evaluated_at
                        ) VALUES (
                            :tid, :ticker, :curr_price, :real_pl, :unreal_pl,
                            :ret_pct, :hold_days, :tp1_hit, :tp1_date, :tp2_hit, :tp2_date,
                            :sl_hit, :sl_date, :max_gain, :max_dd,
                            :pred_res, :pred_res_det, :now
                        )
                    """
                    if hasattr(conn, "conn"):
                        conn.conn.execute(text(insert_str), params)
                    else:
                        conn.execute(text(insert_str), params)
            return True
        except Exception as e:
            print(f"Error saving trade evaluation: {str(e)}")
            return False
