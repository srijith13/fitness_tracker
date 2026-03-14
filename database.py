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
        CREATE TABLE IF NOT EXISTS cardio (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            cardio_name Text NOT NULL,
            cardio_time TEXT NOT NULL,
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

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prs (
            id INTEGER PRIMARY KEY,
            muscle_group_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            exercise_list_id INTEGER NOT NULL,
            best_weight REAL,
            best_reps INTEGER,
            last_updated TEXT  NOT NULL,
            FOREIGN KEY(muscle_group_id) REFERENCES muscle_groups(id)
            FOREIGN KEY(exercise_id) REFERENCES exercises(id)
            FOREIGN KEY(exercise_list_id) REFERENCES exercise_list(id)
        );

        """
    )   

    # -----------------------------
    # Seed data (migration-safe)
    # -----------------------------
    seed_exercises = [
        (1,'bench press',1),
        (2,'close grip bench press',1),
        (3,'incline press',1),
        (4,'decline press',1),
        (5,'push up',1),
        (6,'parallel bar dips',1),
        (7,'dumbbell press',1),
        (8,'dumbbell flys',1),
        (9,'incline dumbbell press',1),
        (10,'incline dumbbell flys',1),
        (11,'pec deck flys',1),
        (12,'cable crossover flys',1),
        (13,'dumbbell pullovers',1),
        (14,'barbell pullovers press',1),
        (15,'chin ups',2),
        (16,'reverse chin ups',2),
        (17,'lat pulldowns',2),
        (18,'back lat pulldowns',2),
        (19,'close grip lat pulldowns',2),
        (20,'straight arm lat pulldowns',2),
        (21,'seated rows',2),
        (22,'one arm dumbbell rows',2),
        (23,'bent rows',2),
        (24,'t-bar rows',2),
        (25,'stiff-legged deadlifts',2),
        (26,'deadlift',2),
        (27,'sumo deadlift',2),
        (28,'back extension',2),
        (29,'chin ups',2),
        (30,'reverse chin ups',2),
        (31,'lat pulldowns',2),
        (32,'back lat pulldowns',2),
        (33,'close grip lat pulldowns',2),
        (34,'straight arm lat pulldowns',2),
        (35,'seated rows',2),
        (36,'one arm dumbbell rows',2),
        (37,'bent rows',2),
        (38,'t-bar rows',2),
        (39,'stiff-legged deadlifts',2),
        (40,'deadlift',2),
        (41,'sumo deadlift',2),
        (42,'back extension',2),
        (43,'back press',3),
        (44,'front press',3),
        (45,'dumbbell press',3),
        (46,'one arm press/arnold press',3),
        (47,'lateral raises',3),
        (48,'bent-over lateral raises',3),
        (49,'front raises',3),
        (50,'side-lying lateral raises',3),
        (51,'low pulley lateral raises',3),
        (52,'low pulley front raises',3),
        (53,'low pulley bent-over lateral raises',3),
        (54,'one dumbbell front raises',3),
        (55,'barbell front raises',3),
        (56,'front press',3),
        (57,'upright rows',3),
        (58,'nautilus lateral raises',3),
        (59,'pec deck rear dealt  laterals',3),
        (60,'barbell shrugs',3),
        (61,'dumbbell shrugs',3),
        (62,'machine shrugs',3),
        (63,'curls',4),
        (64,'concentration curls',4),
        (65,'hammer curls',4),
        (66,'low pulley curls',4),
        (67,'high pulley curls',4),
        (68,'barbell curls',4),
        (69,'machine curls',4),
        (70,'preacher curls',4),
        (71,'reverse curls',4),
        (72,'rope curls',4),
        (73,'pushdowns',5),
        (74,'reverse pushdowns',5),
        (75,'rope pushdowns',5),
        (76,'facing away machine pushdowns',5),
        (77,'one-arm reverse pushdowns',5),
        (78,'triceps extensions',5),
        (79,'dumbbell triceps extensions',5),
        (80,'one-arm tricep extensions',5),
        (81,'seated dumbbell triceps extensions',5),
        (82,'seated ex-bar triceps extensions',5),
        (83,'triceps kickbacks',5),
        (84,'triceps dips',5),
        (85,'reverse wrist curls',6),
        (86,'wrist curls',6),
        (87,'crunches',7),
        (88,'high pulley crunches',7),
        (89,'machine crunches',7),
        (90,'sit ups',7),
        (91,'gym ladder sit ups',7),
        (92,'calves over bench sit ups',7),
        (93,'incline bench sit ups',7),
        (94,'specific bench sit ups',7),
        (95,'leg raises',7),
        (96,'incline leg raises',7),
        (97,'hanging leg raises',7),
        (98,'broomstick twists',7),
        (99,'dumbbell side bends',7),
        (100,'roman chair side bends',7),
        (101,'machine trunk rotations',7),
        (102,'squats',8),
        (103,'dumbbell squats',8),
        (104,'front squats',8),
        (105,'power squats',8),
        (106,'angled leg press',8),
        (107,'hack squats',8),
        (108,'leg extensions',8),
        (109,'seated leg curls',8),
        (110,'lying leg curls',8),
        (111,'standing leg curls',8),
        (112,'good mornings',8),
        (113,'cable adductions',8),
        (114,'machine adductions',8),
        (115,'standing calf raises',8),
        (116,'seated calf raises',8),
        (117,'one leg tow raises',8),
        (118,'donkey calf raises',8),
        (119,'seated barbell calf raises',8),
        (120,'lunges',9),
        (121,'cable back kicks',9),
        (122,'machine hip extensions',9),
        (123,'floor hip extensions',9),
        (124,'bridging',9),
        (125,'cable hip adductions',9),
        (126,'standing machine hip adductions',9),
        (127,'floor hip adductions',9),
        (128,'seated machine hip adductions',9),
        (129,'decline dumbbell press',1),
    ]

    cur.executemany(
        """
        INSERT OR IGNORE INTO exercise_list (id, exercise, muscle_group_id)
        VALUES (?, ?, ?)
        """,
        seed_exercises,
    )

   
    conn.commit()
    conn.close()