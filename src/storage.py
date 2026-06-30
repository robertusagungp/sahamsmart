import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional

class AnalysisStorage:
    """
    Handles persistence of stock analysis logs.
    Supports CSV logging, SQLite, and PostgreSQL (e.g. Neon DB) with graceful fallbacks.
    """
    def __init__(self, db_url: Optional[str] = None, csv_path: str = "data/daily_analysis_log.csv", sqlite_path: str = "data/stock_analysis.db"):
        self.csv_path = csv_path
        self.sqlite_path = sqlite_path
        self.db_url = db_url or os.environ.get("DATABASE_URL")
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.csv_path) or '.', exist_ok=True)
        os.makedirs(os.path.dirname(self.sqlite_path) or '.', exist_ok=True)
        
        # Initialize SQLite/PostgreSQL connections
        self.engine = None
        self._init_db()

    def _init_db(self):
        """
        Initializes the database connection (PostgreSQL or SQLite).
        """
        try:
            from sqlalchemy import create_engine
            
            # Choose database URL
            if self.db_url:
                # Handle Postgres driver naming for SQLAlchemy (replace postgres:// with postgresql://)
                actual_url = self.db_url
                if actual_url.startswith("postgres://"):
                    actual_url = actual_url.replace("postgres://", "postgresql://", 1)
                
                print(f"Connecting to Neon/PostgreSQL database...")
                self.engine = create_engine(actual_url, connect_args={"sslmode": "require"} if "localhost" not in actual_url else {})
            else:
                print(f"Connecting to local SQLite database: {self.sqlite_path}")
                self.engine = create_engine(f"sqlite:///{self.sqlite_path}")
            
            # Create table if it doesn't exist
            self._create_table_if_not_exists()
        except Exception as e:
            print(f"Warning: Failed to initialize database: {str(e)}. Falling back to CSV-only operations.")
            self.engine = None

    def _create_table_if_not_exists(self):
        if not self.engine:
            return
        try:
            from sqlalchemy import MetaData, Table, Column, Integer, Float, String, Date
            metadata = MetaData()
            
            # Define Table
            self.table = Table(
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
            metadata.create_all(self.engine)
        except Exception as e:
            print(f"Error creating table: {str(e)}")
            self.engine = None

    def save_analysis(self, records: List[Dict[str, Any]]) -> bool:
        """
        Save daily stock analysis records to Database and CSV.
        """
        if not records:
            return False
            
        success_db = False
        success_csv = False
        
        # 1. Prepare data
        df = pd.DataFrame(records)
        # Standardize columns
        required_cols = [
            'tanggal', 'ticker', 'close_price', 'rsi', 'ma20', 'ma50', 
            'momentum_1m', 'momentum_3m', 'volume_ratio', 'score', 'recommendation'
        ]
        
        # Fill missing required columns with None if any
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        df = df[required_cols].copy()
        
        # Convert date to date object for DB or string for CSV
        df['tanggal'] = pd.to_datetime(df['tanggal']).dt.date
        
        # 2. Save to Database
        if self.engine:
            try:
                # Save to SQL
                df.to_sql('stock_analysis_logs', con=self.engine, if_exists='append', index=False)
                success_db = True
                print("Successfully saved analysis to database.")
            except Exception as e:
                print(f"Error saving to database: {str(e)}")
        
        # 3. Save to CSV
        try:
            csv_df = df.copy()
            # Convert date to string for CSV compatibility
            csv_df['tanggal'] = csv_df['tanggal'].apply(lambda x: x.strftime('%Y-%m-%d') if hasattr(x, 'strftime') else str(x))
            
            if os.path.exists(self.csv_path):
                # Append to existing CSV, avoiding duplicate rows for the same date and ticker
                existing_df = pd.read_csv(self.csv_path)
                combined = pd.concat([existing_df, csv_df], ignore_index=True)
                # Drop duplicates for same day + ticker, keeping the latest run
                combined = combined.drop_duplicates(subset=['tanggal', 'ticker'], keep='last')
                combined.to_csv(self.csv_path, index=False)
            else:
                csv_df.to_csv(self.csv_path, index=False)
            success_csv = True
            print(f"Successfully saved analysis to CSV: {self.csv_path}")
        except Exception as e:
            print(f"Error saving to CSV: {str(e)}")
            
        return success_db or success_csv

    def load_historical_logs(self, limit: int = 500) -> pd.DataFrame:
        """
        Load historical analysis logs from the database, or fallback to CSV.
        """
        if self.engine:
            try:
                query = f"SELECT tanggal, ticker, close_price, rsi, ma20, ma50, momentum_1m, momentum_3m, volume_ratio, score, recommendation FROM stock_analysis_logs ORDER BY tanggal DESC, score DESC LIMIT {limit}"
                df = pd.read_sql(query, con=self.engine)
                return df
            except Exception as e:
                print(f"Failed to query database: {str(e)}. Falling back to CSV.")
                
        if os.path.exists(self.csv_path):
            try:
                df = pd.read_csv(self.csv_path)
                df = df.sort_values(by=['tanggal', 'score'], ascending=[False, False])
                return df.head(limit)
            except Exception as e:
                print(f"Failed to read CSV: {str(e)}")
                
        return pd.DataFrame()
