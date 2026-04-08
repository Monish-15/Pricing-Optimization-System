import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "pricing_system.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS demand_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            demand INTEGER,
            supply INTEGER,
            time_of_day TEXT,
            price REAL,
            actual_sales INTEGER,
            revenue REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT,
            rmse REAL,
            r2 REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
