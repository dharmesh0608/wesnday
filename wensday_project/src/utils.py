import sqlite3
from datetime import datetime
from config import DB_PATH, NOTES_PATH
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS alarms (id TEXT PRIMARY KEY, run_at TEXT)''')
    conn.commit(); conn.close()
def save_alarm(alarm_id, when):
    conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
    cur.execute('INSERT OR REPLACE INTO alarms (id, run_at) VALUES (?,?)', (alarm_id, str(when)))
    conn.commit(); conn.close()
def delete_alarm(alarm_id):
    conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
    cur.execute('DELETE FROM alarms WHERE id = ?', (alarm_id,))
    deleted = cur.rowcount > 0
    conn.commit(); conn.close()
    return deleted
def list_alarms():
    conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
    cur.execute('SELECT id, run_at FROM alarms'); rows = cur.fetchall(); conn.close()
    return [{'id':r[0],'when':r[1]} for r in rows]
def save_note(text):
    import json, os
    notes = []
    if os.path.exists(NOTES_PATH):
        try:
            with open(NOTES_PATH, 'r', encoding='utf-8') as notes_file:
                notes = json.load(notes_file)
        except (OSError, json.JSONDecodeError): notes = []
    notes.append({'text':text,'created':str(datetime.now())})
    with open(NOTES_PATH, 'w', encoding='utf-8') as notes_file:
        json.dump(notes, notes_file, indent=2)
def read_notes():
    import json, os
    if not os.path.exists(NOTES_PATH): return []
    try:
        with open(NOTES_PATH, 'r', encoding='utf-8') as notes_file:
            return json.load(notes_file)
    except (OSError, json.JSONDecodeError):
        return []
# initialize
init_db()
