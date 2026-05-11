import pandas as pd
from sqlalchemy import create_engine
import os

DB_FILE = "telemetry_db.sqlite"
OUTPUT_FILE = "exported_telemetry.csv"

def export_to_csv():
    """Exports data from SQLite to CSV."""
    if not os.path.exists(DB_FILE):
        print(f"Error: {DB_FILE} not found. Run the ETL pipeline or simulation first.")
        return

    print(f"Connecting to {DB_FILE}...")
    engine = create_engine(f"sqlite:///{DB_FILE}")
    
    try:
        print("Reading data (this may take a moment)...")
        # Select all data
        df = pd.read_sql("SELECT * FROM telemetry", engine)
        
        if df.empty:
            print("Database is empty. No data to export.")
            return

        print(f"saving {len(df)} records to {OUTPUT_FILE}...")
        df.to_csv(OUTPUT_FILE, index=False)
        print("✅ Export Complete.")
        
    except Exception as e:
        print(f"Error during export: {e}")

if __name__ == "__main__":
    export_to_csv()
