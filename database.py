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
        CREATE TABLE IF NOT EXISTS muscle_groups (
            id INTEGER PRIMARY KEY,
            muscle_group TEXT,
            mg_image BLOB
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS exercise_list (
            id INTEGER PRIMARY KEY,
            exercise TEXT,
            muscle_group_id INTEGER,
            FOREIGN KEY(muscle_group_id) REFERENCES muscle_groups(id)
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
            notes TEXT,
            exercise_list_id INTEGER,
            muscle_group_id INTEGER,
            FOREIGN KEY(exercise_list_id) REFERENCES exercise_list(id)
            FOREIGN KEY(muscle_group_id) REFERENCES muscle_groups(id)
        )
        """
    )

    conn.commit()
    conn.close()