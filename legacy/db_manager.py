import sqlite3
from sqlite3 import Error
import os

DB_FILE = "telemetry_db.sqlite"

def create_connection():
    """Create a database connection to the SQLite database specified by DB_FILE"""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_table(conn, create_table_sql):
    """Create a table from the create_table_sql statement"""
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(f"Error creating table: {e}")

def setup_database():
    """Initializes the database with the required schema."""
    sql_create_telemetry_table = """
    CREATE TABLE IF NOT EXISTS telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME NOT NULL,
        vehicle_id TEXT NOT NULL,
        sensor_id TEXT NOT NULL,
        temperature_c REAL,
        voltage_v REAL,
        vibration_g REAL,
        latitude REAL,
        longitude REAL,
        status TEXT
    );
    """
    
    # Index for faster querying
    sql_create_index = "CREATE INDEX IF NOT EXISTS idx_vehicle_time ON telemetry (vehicle_id, timestamp);"

    conn = create_connection()

    if conn is not None:
        create_table(conn, sql_create_telemetry_table)
        create_table(conn, sql_create_index)
        print("✅ Database and tables created successfully.")
        conn.close()
    else:
        print("Error! cannot create the database connection.")

if __name__ == "__main__":
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE) # Clean slate for this run
        print("Removed existing database.")
    setup_database()
