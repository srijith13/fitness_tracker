import csv
from pathlib import Path
from models import list_weights, list_exercises, add_weight_entry, add_exercise

EXPORT_PATH = Path(__file__).parent / "data"

# Export -------------------------------------------------------------

def export_all():
    wp = EXPORT_PATH / "weights.csv"
    ep = EXPORT_PATH / "exercises.csv"

    with wp.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "weight_kg", "notes"])
        for r in list_weights():
            w.writerow([r['date'], r['weight_kg'], r.get('notes','')])

    with ep.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date","name","sets_completed","sets_json","notes"])
        for r in list_exercises():
            w.writerow([r['date'], r['name'], r['sets_completed'], r['sets_json'], r.get('notes','')])

    return str(wp), str(ep)

# Import -------------------------------------------------------------

def import_weights(file_path):
    with open(file_path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            add_weight_entry(r['date'], float(r['weight_kg']), r.get('notes'))

def import_exercises(file_path):
    import json
    with open(file_path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            sets = json.loads(r['sets_json'])
            add_exercise(r['date'], r['name'], int(r['sets_completed']), sets, r.get('notes'))
