import pandas as pd
import sqlite3
from db_manager import create_connection, setup_database, DB_FILE
import os

DATA_FILE = "telemetry_data.csv"

def run_etl_pipeline():
    """Reads data from CSV and loads it into SQLite."""
    print("Starting ETL Pipeline...")

    # 1. Initialize DB
    if not os.path.exists(DB_FILE):
        print("Database not found, setting up...")
        setup_database()
    
    # 2. Extract (Read CSV)
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found. Please run data_generator.py first.")
        return

    print(f"reading {DATA_FILE}...")
    chunk_size = 50000 
    conn = create_connection()
    
    if conn is None:
        print("Failed to connect to DB.")
        return

    # 3. Load (Insert into SQLite)
    # Using chunking to handle large files efficiently
    count = 0
    for chunk in pd.read_csv(DATA_FILE, chunksize=chunk_size):
        chunk.to_sql('telemetry', conn, if_exists='append', index=False)
        count += len(chunk)
        print(f"Processed {count} records...")

    conn.close()
    print(f"✅ ETL Complete. {count} records loaded into {DB_FILE}")

if __name__ == "__main__":
    # Ensure DB is fresh for this run
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        setup_database()
        
    run_etl_pipeline()
