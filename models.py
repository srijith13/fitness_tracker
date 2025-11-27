import json
from database import get_conn

# Weight ------------------------------------------------------

def add_weight_entry(date: str, weight_kg: float, notes: str | None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO weight (date, weight_kg, notes) VALUES (?, ?, ?)",
        (date, weight_kg, notes)
    )
    conn.commit()
    conn.close()

def list_weights(limit=2000):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM weight ORDER BY date ASC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Exercises ----------------------------------------------------

def add_exercise(date: str, name: str, sets_completed: int, sets: list, notes: str | None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO exercises (date, name, sets_completed, sets_json, notes) VALUES (?, ?, ?, ?, ?)",
        (date, name, sets_completed, json.dumps(sets), notes)
    )
    conn.commit()
    conn.close()

def list_exercises(limit=2000):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM exercises ORDER BY date ASC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["sets"] = json.loads(d["sets_json"] or "[]")
        result.append(d)
    return result

# Auto PR detection --------------------------------------------------

def detect_prs():
    exercises = list_exercises()
    prs = {}
    for ex in exercises:
        name = ex["name"].lower()
        for s in ex["sets"]:
            wt = float(s.get("weight", 0))
            if wt > prs.get(name, 0):
                prs[name] = wt
    return prs