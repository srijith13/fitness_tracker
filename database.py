import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "tracker.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS weight (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            weight_kg REAL NOT NULL,
            notes TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            name TEXT NOT NULL,
            sets_completed INTEGER,
            sets_json TEXT,
            notes TEXT
        )
        """
    )

    conn.commit()
    conn.close()