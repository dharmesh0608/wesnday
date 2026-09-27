from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import webbrowser
from datetime import datetime
from urllib.parse import quote

from apscheduler.schedulers.background import BackgroundScheduler

from utils import delete_alarm, list_alarms, save_alarm, save_note, read_notes

scheduler = BackgroundScheduler(daemon=True)
scheduler.start()
ACTIONS = {}
_alarm_notifier = print


def set_alarm_notifier(notifier):
    global _alarm_notifier
    _alarm_notifier = notifier


def action(name):
    def register(function):
        ACTIONS[name] = function
        return function
    return register


def _alarm_job(when):
    _alarm_notifier(f"Wensday alarm: {when:%I:%M %p}")


def _restore_alarms():
    now = datetime.now()
    for alarm in list_alarms():
        try:
            when = datetime.fromisoformat(alarm["when"])
        except (KeyError, TypeError, ValueError):
            continue
        if when > now:
            scheduler.add_job(_alarm_job, "date", run_date=when, args=[when], id=alarm["id"],
                              replace_existing=True)


_restore_alarms()


@action("set_alarm")
def set_alarm(entities):
    when = entities.get("time")
    if not when:
        return {"status": "fail", "say": "I could not parse the time for the alarm."}
    job_id = f"alarm-{int(when.timestamp())}"
    scheduler.add_job(_alarm_job, "date", run_date=when, args=[when], id=job_id,
                      replace_existing=True)
    save_alarm(job_id, when)
    return {"status": "ok", "say": f"Alarm set for {when:%A at %I:%M %p}.", "alarm_id": job_id}


@action("list_alarms")
def list_alarm_action(entities):
    alarms = list_alarms()
    if not alarms:
        return {"status": "ok", "say": "No alarms are set.", "alarms": []}
    details = "; ".join(f"{alarm['id']}: {alarm['when']}" for alarm in alarms)
    return {"status": "ok", "say": f"You have {len(alarms)} alarm(s): {details}", "alarms": alarms}


@action("cancel_alarm")
def cancel_alarm(entities):
    alarms = list_alarms()
    alarm_id = entities.get("alarm_id")
    if not alarm_id:
        if len(alarms) != 1:
            message = "No alarms are set." if not alarms else "Please specify the alarm ID from your alarm list."
            return {"status": "fail", "say": message, "alarms": alarms}
        alarm_id = alarms[0]["id"]
    if not delete_alarm(alarm_id):
        return {"status": "fail", "say": "I could not find that alarm."}
    try:
        scheduler.remove_job(alarm_id)
    except Exception:
        pass
    return {"status": "ok", "say": "Alarm cancelled."}


@action("open_app")
def open_app(entities):
    text = (entities.get("app_name") or entities.get("text", "")).lower()
    if "youtube" in text:
        webbrowser.open("https://www.youtube.com")
        return {"status": "ok", "say": "Opening YouTube."}
    if "google" in text or "browser" in text:
        webbrowser.open("https://www.google.com")
        return {"status": "ok", "say": "Opening Google."}

    if "chrome" in text:
        executable = shutil.which("chrome") or shutil.which("google-chrome")
        if executable:
            subprocess.Popen([executable])
            return {"status": "ok", "say": "Opening Chrome."}
        if platform.system() == "Windows":
            candidates = (
                os.path.expandvars(r"%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe"),
            )
            for path in candidates:
                if os.path.isfile(path):
                    subprocess.Popen([path])
                    return {"status": "ok", "say": "Opening Chrome."}
    if "calculator" in text:
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["calc.exe"])
            else:
                executable = shutil.which("gnome-calculator") or shutil.which("kcalc")
                if not executable:
                    raise FileNotFoundError
                subprocess.Popen([executable])
            return {"status": "ok", "say": "Opening Calculator."}
        except OSError:
            pass
    return {"status": "fail", "say": "I could not find that app to open."}


@action("take_note")
def take_note(entities):
    text = entities.get("note_text") or entities.get("text")
    if not text:
        return {"status": "fail", "say": "No note text provided."}
    save_note(text)
    return {"status": "ok", "say": "Note saved."}


@action("show_notes")
def show_notes(entities):
    notes = read_notes()
    if not notes:
        return {"status": "ok", "say": "You have no notes.", "notes": []}
    return {"status": "ok", "say": f"You have {len(notes)} notes.", "notes": notes}


def _phone_number(text):
    match = re.search(r"(?:\+?\d[\d ()-]{6,}\d)", text)
    if not match:
        return None
    number = re.sub(r"[ ()-]", "", match.group(0))
    return number if len(re.sub(r"\D", "", number)) >= 7 else None


@action("make_call")
def make_call(entities):
    number = _phone_number(entities.get("text", ""))
    if not number:
        return {"status": "fail", "say": "Say a phone number; contact names are not configured yet."}
    opened = webbrowser.open(f"tel:{number}")
    return {"status": "ok" if opened else "fail",
            "say": "Opening the phone app to review the call." if opened else "No phone app accepted the call handoff."}


@action("send_message")
def send_message(entities):
    text = entities.get("text", "")
    number = _phone_number(text)
    if not number:
        return {"status": "fail", "say": "Say a phone number; contact names are not configured yet."}
    message_match = re.search(r":\s*(.+)$", text)
    body = quote(message_match.group(1)) if message_match else ""
    opened = webbrowser.open(f"sms:{number}?body={body}")
    return {"status": "ok" if opened else "fail",
            "say": "Opening the messaging app to review the message." if opened else "No messaging app accepted the handoff."}


@action("show_calendar")
def show_calendar(entities):
    try:
        from calendar_service import upcoming_events

        events = upcoming_events()
    except ImportError:
        return {"status": "fail", "say": "Install the Google Calendar optional dependencies first."}
    except Exception as exc:
        return {"status": "fail", "say": f"Calendar access failed: {exc}"}
    if not events:
        return {"status": "ok", "say": "There are no upcoming calendar events.", "events": []}
    return {"status": "ok", "say": "Upcoming events: " + "; ".join(events), "events": events}
