import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'alarms.db')
NOTES_PATH = os.path.join(DATA_DIR, 'notes.json')
# Theme
COLOR_BG = '#000000'
COLOR_ACCENT = '#0a84ff'
COLOR_TEXT = '#ffffff'
# Twilio (optional)
TWILIO_ACCOUNT = ''
TWILIO_TOKEN = ''
TWILIO_FROM = ''
WAKE_WORD = 'wensday'
LANG = 'en-IN'
