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

def list_weights_date(start, end):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("select  * from weight WHERE  date BETWEEN ? AND ? ORDER BY date ASC LIMIT 31", (start, end))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Muscle Group ----------------------------------------------------

def list_muscle_group():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM  muscle_groups ORDER BY id asc")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def list_muscle_exercises(muscle_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM  exercise_list WHERE muscle_group_id = ?  ORDER BY id asc", (muscle_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Exercises ----------------------------------------------------

def add_exercise(date: str, name: str, sets_completed: int, sets: list, notes: str,muscle_group_id:int | None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO exercises (date, name, sets_completed, sets_json, notes,  muscle_group_id) VALUES (?, ?, ?, ?, ?, ?)",
        (date, name, sets_completed, json.dumps(sets), notes,muscle_group_id)
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

def list_exercises_for_prs(id,limit=20):
    conn = get_conn()
    cur = conn.cursor()

    if id is not None:
        cur.execute("SELECT * FROM exercises ex JOIN muscle_groups mg ON mg.id = ex.muscle_group_id where mg.id = ?  ORDER BY date ASC LIMIT ?", (id,limit,))
    else:
        cur.execute("SELECT * FROM exercises ex JOIN muscle_groups mg ON mg.id = ex.muscle_group_id  ORDER BY date ASC LIMIT ?", (limit,))


    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["sets"] = json.loads(d["sets_json"] or "[]")
        result.append(d)
    return result

def list_exercises_date(start,end):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM exercises WHERE  date BETWEEN ? AND ? ORDER BY date ASC LIMIT 31", (start,end))
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


# insert_icon("D:/Learning/GOLANG/Health Tracker/fitness_tracker_app/data/fitnessapp_images/abdominals/abdominals.ico", 7)

# # test 
# def insert_icon(path_to_ico: str, id: int):
#     conn = get_conn()
#     cur = conn.cursor()

#     # Read the .ico file as binary
#     with open(path_to_ico, "rb") as f:
#         ico_bytes = f.read()

#     cur.execute(
#         "UPDATE muscle_groups SET mg_image = ? WHERE id = ?",
#         (ico_bytes, id)
#     )

#     conn.commit()
#     conn.close()