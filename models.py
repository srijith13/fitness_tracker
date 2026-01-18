import json
from database import get_conn
import base64
from PIL import Image
import io

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

def list_weights(limit=100):
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

# Cardio ------------------------------------------------------

def add_cardio_entry(date: str, cardio_name: str, notes: str, cardio_time: str | None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO cardio (date, cardio_name, cardio_time, notes) VALUES (?, ?, ?, ?)",
        (date, cardio_name, cardio_time, notes)
    )
    conn.commit()
    conn.close()

def list_cardio(limit=100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cardio ORDER BY date ASC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def list_cardio_date(start, end):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("select  * from cardio WHERE  date BETWEEN ? AND ? ORDER BY date ASC LIMIT 31", (start, end))
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

def add_exercise(date: str, name: str, sets_completed: int, sets: list, notes: str,exercise_list_id:int,muscle_group_id:int | None):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO exercises (date, name, sets_completed, sets_json, notes, exercise_list_id, muscle_group_id) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id""", 
        (date,name,sets_completed,json.dumps(sets),notes,exercise_list_id,muscle_group_id,)
        )

    new_id = cur.fetchone()[0]   
    conn.commit()

    best_set = current_best_set(conn, exercise_list_id)

    if best_set:
        best_weight, best_reps = best_set
        update_best_set(conn,muscle_group_id,new_id,exercise_list_id,best_weight,best_reps,date)
    
    conn.close()


def current_best_set(conn, exercise_list_id):
    cur = conn.cursor()

    cur.execute("""
        WITH expanded AS (
            SELECT
                e.id,
                e.date,
                e.name,
                json_extract(j.value, '$.weight') AS weight,
                json_extract(j.value, '$.reps')   AS reps
            FROM exercises e
            JOIN json_each(e.sets_json) j
            WHERE e.exercise_list_id = ?
        ),
        ranked AS (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY date, name
                       ORDER BY weight DESC, reps DESC
                   ) AS rn
            FROM expanded
        )
                
        SELECT max(weight), reps FROM ranked WHERE rn = 1 ORDER BY weight DESC
    """, (exercise_list_id,))

    row = cur.fetchone()
    return row 


def update_best_set(conn,muscle_group_id,exercise_id,exercise_list_id,new_weight,new_reps,date):
    cur = conn.cursor()
    cur.execute("""SELECT id, best_weight, best_reps FROM prs WHERE exercise_list_id = ? """, (exercise_list_id,))
    row = cur.fetchone()

    if row is None:
        cur.execute("""INSERT INTO prs (muscle_group_id, exercise_id, exercise_list_id, best_weight, best_reps, last_updated)  VALUES (?, ?, ?, ?, ?, ?)""", 
                    (muscle_group_id,exercise_id,exercise_list_id,new_weight,new_reps,date))
        conn.commit()
        return

    pr_id, old_weight, old_reps = row

    is_better = (new_weight > old_weight or(new_weight == old_weight and new_reps > old_reps))

    if is_better:
        cur.execute("""UPDATE prs SET best_weight = ?,best_reps = ?,exercise_id = ?,last_updated = ? WHERE id = ?""", 
                    (new_weight,new_reps,exercise_id,date,pr_id))
        conn.commit()


# def list_exercises(limit=2000):
#     conn = get_conn()
#     cur = conn.cursor()
#     cur.execute("SELECT * FROM exercises ORDER BY date ASC LIMIT ?", (limit,))
#     rows = cur.fetchall()
#     conn.close()

#     result = []
#     for r in rows:
#         d = dict(r)
#         d["sets"] = json.loads(d["sets_json"] or "[]")
#         result.append(d)
#     return result

def list_exercises(limit=2000):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""SELECT ex.*,
                    CASE
                        WHEN p.exercise_id IS NOT NULL THEN 1
                        ELSE 0
                    END AS is_pr
                FROM exercises ex LEFT JOIN prs p ON p.exercise_id = ex.id ORDER BY ex.date DESC LIMIT ?;""", (limit,))
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
        cur.execute("""SELECT ex.*, mg.*, p.best_weight,p.best_reps  FROM exercises ex JOIN muscle_groups mg ON mg.id = ex.muscle_group_id 
                    JOIN prs p ON p.exercise_id = ex.id  where mg.id = ?  
                    ORDER BY date ASC LIMIT ?""", (id,limit,))
    else:
        cur.execute("""SELECT ex.*, mg.*, p.best_weight,p.best_reps  FROM exercises ex JOIN muscle_groups mg ON mg.id = ex.muscle_group_id 
                    JOIN prs p ON p.exercise_id = ex.id  
                    ORDER BY date ASC LIMIT ?""", (limit,))


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
    cur.execute("""SELECT ex.*,
                    CASE
                        WHEN p.exercise_id IS NOT NULL THEN 1
                        ELSE 0
                    END AS is_pr 
                FROM exercises ex LEFT JOIN prs p ON p.exercise_id = ex.id WHERE  date BETWEEN ? AND ? ORDER BY date ASC LIMIT 31""", (start,end))
    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["sets"] = json.loads(d["sets_json"] or "[]")
        result.append(d)
    return result


def list_muscle_group_date(start,end):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""SELECT mg.*,ex.date,
                    CASE
                        WHEN p.exercise_id IS NOT NULL THEN 1
                        ELSE 0
                    END AS is_pr 
                FROM exercises ex LEFT JOIN prs p ON p.exercise_id = ex.id  JOIN muscle_groups mg on mg.id = ex.muscle_group_id
                WHERE  date BETWEEN ? AND ? GROUP BY mg.id, ex.date ORDER BY date ASC LIMIT 31""", (start,end))
    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
       
        d = dict(r)
        png_base_64  =png_converter(d.get('mg_image'))
        d["mg_image"] = png_base_64
        result.append(d)
    return result

def list_mg_exercises_date(mg_id,date):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""SELECT ex.*,
                    CASE
                        WHEN p.exercise_id IS NOT NULL THEN 1
                        ELSE 0
                    END AS is_pr 
                FROM exercises ex LEFT JOIN prs p ON p.exercise_id = ex.id  JOIN muscle_groups mg on mg.id = ex.muscle_group_id where mg.id = ? AND 
                ex.date = ? ORDER BY ex.date ASC LIMIT 31""", (mg_id,date))
    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["sets"] = json.loads(d["sets_json"] or "[]")
        result.append(d)
    return result

def png_converter(ico_bytes):
    # 2. Convert ICO → PNG in memory
    ico_image = Image.open(io.BytesIO(ico_bytes))
    png_buffer = io.BytesIO()
    ico_image.save(png_buffer, format="PNG")
    png_base64 = base64.b64encode(png_buffer.getvalue()).decode()
    return png_base64

# Auto PR detection --------------------------------------------------
# UPdated in above code to get from db directly
# def detect_prs(days_limit):
#     exercises = list_exercises(days_limit)
#     prs = {}
#     for ex in exercises:
#         name = ex["name"].lower()
#         for s in ex["sets"]:
#             wt = float(s.get("weight", 0))
#             if wt > prs.get(name, 0):
#                 prs[name] = wt
#     return prs


######### for creating prs table
#     WITH expanded AS (
#     SELECT
#         e.id,
#         e.date,
#         e.name,
#         e.muscle_group_id,
#         e.exercise_list_id,
#         json_extract(j.value, '$.weight') AS weight,
#         json_extract(j.value, '$.reps')   AS reps
#     FROM exercises e
#     JOIN json_each(e.sets_json) j
# ),
# ranked AS (
#     SELECT *,
#            ROW_NUMBER() OVER (
#                PARTITION BY name
#                ORDER BY weight DESC, reps DESC
#            ) AS rn
#     FROM expanded
# )
# INSERT INTO prs (
#     muscle_group_id,
#     exercise_id,
#     exercise_list_id,
#     best_weight,
#     best_reps,
#     last_updated
# )
# SELECT
#     muscle_group_id,
#     id,
#     exercise_list_id,
#     weight,
#     reps,
#     date
# FROM ranked
# WHERE rn = 1
# ON CONFLICT(exercise_list_id)
# DO UPDATE SET
#     best_weight = excluded.best_weight,
#     best_reps   = excluded.best_reps,
#     last_updated = excluded.last_updated;


# -- 		CREATE UNIQUE INDEX IF NOT EXISTS idx_prs_exercise
# -- ON prs (exercise_list_id)


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

