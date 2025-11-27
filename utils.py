from datetime import date, datetime

def iso_today():
    return date.today().isoformat()

def now_iso():
    return datetime.now().isoformat()
