"""Minimal Kivy Android client for Wensday's core local commands."""

from __future__ import annotations

import json
import importlib
import re
import sys
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput


ACCENT = (0.02, 0.49, 0.94, 1)
SURFACE = (0.07, 0.09, 0.12, 1)
TEXT = (0.94, 0.96, 0.99, 1)


class WensdayAndroidApp(App):
    def build(self):
        Window.clearcolor = (0.015, 0.02, 0.03, 1)
        self.state_path = Path(self.user_data_dir) / "wensday-state.json"
        self.state = self._load_state()

        root = BoxLayout(orientation="vertical", padding=16, spacing=10)
        title = TextInput(
            text="WENSDAY  /  MOBILE",
            readonly=True,
            multiline=False,
            size_hint_y=None,
            height=48,
            background_color=SURFACE,
            foreground_color=ACCENT,
            font_size=18,
        )
        self.transcript = TextInput(
            text="Wensday is ready. Try 'note buy milk' or 'set alarm for 7:30 am'.\n",
            readonly=True,
            background_color=SURFACE,
            foreground_color=TEXT,
            cursor_color=ACCENT,
            font_size=16,
        )
        self.command = TextInput(
            hint_text="Enter a command",
            multiline=False,
            size_hint_y=None,
            height=52,
            background_color=SURFACE,
            foreground_color=TEXT,
            cursor_color=ACCENT,
            font_size=16,
        )
        self.command.bind(on_text_validate=lambda *_: self.submit())

        controls = BoxLayout(size_hint_y=None, height=48, spacing=10)
        send = Button(text="Send", background_normal="", background_color=ACCENT)
        send.bind(on_release=lambda *_: self.submit())
        help_button = Button(text="Commands", background_normal="", background_color=SURFACE)
        help_button.bind(on_release=lambda *_: self.respond(self.help_text()))
        controls.add_widget(help_button)
        controls.add_widget(send)

        root.add_widget(title)
        root.add_widget(self.transcript)
        root.add_widget(self.command)
        root.add_widget(controls)
        self._restore_alarms()
        return root

    def _load_state(self):
        try:
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
            if isinstance(state, dict):
                state.setdefault("notes", [])
                state.setdefault("alarms", [])
                return state
        except (OSError, json.JSONDecodeError):
            pass
        return {"notes": [], "alarms": []}

    def _save_state(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def _restore_alarms(self):
        now = datetime.now()
        pending = []
        for alarm in self.state["alarms"]:
            try:
                when = datetime.fromisoformat(alarm["when"])
            except (KeyError, TypeError, ValueError):
                continue
            if when > now:
                pending.append(alarm)
                Clock.schedule_once(lambda _dt, item=alarm: self._fire_alarm(item), (when - now).total_seconds())
        self.state["alarms"] = pending
        self._save_state()

    def _fire_alarm(self, alarm):
        if alarm not in self.state["alarms"]:
            return
        self.state["alarms"].remove(alarm)
        self._save_state()
        self.respond(f"Alarm: {alarm['label']}.")

    def _say(self, message):
        self.transcript.text += f"Wensday: {message}\n"
        self.transcript.cursor = (0, len(self.transcript.text.splitlines()))

    def respond(self, message):
        self._say(message)

    @staticmethod
    def help_text():
        return "Try: note <text>, show notes, set alarm for <time>, list alarms, cancel alarm, open Google/YouTube, call <number>, or text <number>: <message>."

    def submit(self):
        text = self.command.text.strip()
        self.command.text = ""
        if not text:
            return
        self.transcript.text += f"You: {text}\n"
        lowered = text.lower()

        if lowered in {"help", "commands"}:
            self.respond(self.help_text())
        elif lowered.startswith(("note ", "remember ")):
            note = re.sub(r"^(note|remember)\s+", "", text, flags=re.I).strip()
            if note:
                self.state["notes"].append({"text": note, "created": datetime.now().isoformat(timespec="seconds")})
                self._save_state()
                self.respond("Note saved.")
            else:
                self.respond("Tell me what to save.")
        elif lowered in {"show notes", "list notes", "read notes"}:
            notes = self.state["notes"]
            self.respond("No notes saved." if not notes else "Notes: " + "; ".join(note["text"] for note in notes))
        elif "alarm" in lowered and any(word in lowered for word in ("set", "wake", "alarm for")):
            self._set_alarm(text)
        elif "alarm" in lowered and any(word in lowered for word in ("list", "show")):
            alarms = self.state["alarms"]
            self.respond("No alarms set." if not alarms else "Alarms: " + "; ".join(alarm["label"] for alarm in alarms))
        elif "cancel alarm" in lowered:
            self._cancel_alarm()
        elif "youtube" in lowered and lowered.startswith("open "):
            self._open_url("https://www.youtube.com")
        elif "google" in lowered and lowered.startswith("open "):
            self._open_url("https://www.google.com")
        elif lowered.startswith(("call ", "dial ")):
            self._phone_handoff(text, sms=False)
        elif lowered.startswith(("text ", "sms ", "message ")):
            self._phone_handoff(text, sms=True)
        else:
            self.respond("That command is not supported in the mobile starter yet. Type 'commands' for the available set.")

    def _set_alarm(self, text):
        match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", text, re.I)
        if not match:
            self.respond("Say a time such as 7:30 am or 19:30.")
            return
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        period = (match.group(3) or "").lower()
        if minute > 59 or hour > (12 if period else 23) or (period and hour == 0):
            self.respond("That time is not valid.")
            return
        if period:
            hour = hour % 12 + (12 if period == "pm" else 0)
        now = datetime.now()
        when = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if when <= now:
            when += timedelta(days=1)
        alarm = {"when": when.isoformat(timespec="seconds"), "label": when.strftime("%b %d at %I:%M %p")}
        self.state["alarms"].append(alarm)
        self._save_state()
        Clock.schedule_once(lambda _dt: self._fire_alarm(alarm), (when - now).total_seconds())
        self.respond(f"Alarm set for {alarm['label']}. It will alert while Wensday is open.")

    def _cancel_alarm(self):
        if not self.state["alarms"]:
            self.respond("No alarms set.")
            return
        alarm = min(self.state["alarms"], key=lambda item: item["when"])
        self.state["alarms"].remove(alarm)
        self._save_state()
        self.respond(f"Cancelled the next alarm ({alarm['label']}).")

    def _phone_handoff(self, text, sms):
        match = re.search(r"\+?\d[\d ()-]{6,}\d", text)
        if not match:
            self.respond("Include a phone number in the command.")
            return
        number = re.sub(r"[ ()-]", "", match.group(0))
        if len(re.sub(r"\D", "", number)) < 7:
            self.respond("That phone number looks too short.")
            return
        message_match = re.search(r":\s*(.+)$", text)
        body = message_match.group(1) if message_match else ""
        if self._android_intent(number, body if sms else None):
            self.respond("Review and confirm in your phone app." if sms else "Review and place the call in your dialer.")

    def _android_intent(self, number_or_url, message=None):
        if not hasattr(sys, "getandroidapilevel"):
            uri = f"sms:{number_or_url}" if message is not None else f"tel:{number_or_url}"
            if message:
                uri += "?body=" + message
            self.respond(f"Android handoff requested: {uri}")
            return True
        try:
            autoclass = importlib.import_module("jnius").autoclass

            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            intent_class = autoclass("android.content.Intent")
            uri_class = autoclass("android.net.Uri")
            if number_or_url.startswith(("https://", "http://")):
                intent = intent_class("android.intent.action.VIEW")
                intent.setData(uri_class.parse(number_or_url))
            elif message is None:
                intent = intent_class("android.intent.action.DIAL")
                intent.setData(uri_class.parse(f"tel:{number_or_url}"))
            else:
                intent = intent_class("android.intent.action.SENDTO")
                intent.setData(uri_class.parse(f"smsto:{number_or_url}"))
                intent.putExtra("sms_body", message)
            activity.startActivity(intent)
            return True
        except Exception as exc:
            self.respond(f"Could not open the Android app: {exc}")
            return False

    def _open_url(self, url):
        if hasattr(sys, "getandroidapilevel"):
            if self._android_intent(url):
                self.respond(f"Opening {url}.")
        elif webbrowser.open(url):
            self.respond(f"Opening {url}.")
        else:
            self.respond(f"Open this address in your browser: {url}")


if __name__ == "__main__":
    WensdayAndroidApp().run()