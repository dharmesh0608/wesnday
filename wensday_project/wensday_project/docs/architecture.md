# Architecture

## Desktop

- `src/main.py` loads `.env`, creates the Qt application, and wires speech, assistant, and UI.
- `src/gui.py` provides text input, asynchronous microphone capture, and an optional wake-word control.
- `src/assistant.py` matches `src/intents.json`, extracts entities, dispatches local actions, and falls back to OpenAI when configured.
- `src/actions.py` owns alarms, notes, app/web launching, phone/SMS handoffs, and Calendar dispatch.
- `src/utils.py` stores alarms in SQLite and notes in JSON under `src/data/`.
- `src/speech.py`, `src/wake_word.py`, `src/ai.py`, and `src/calendar_service.py` isolate optional services.

## Android

`android/main.py` is a standalone Kivy client and does not import the PyQt desktop modules. It keeps notes and foreground alarm state in private JSON storage and uses Android intents for dialer, SMS composer, and browser handoffs. Alarms only notify while the app process is active; background services and desktop feature parity are not included.

## External Services and Secrets

OpenAI answers, Picovoice wake-word detection, and Google Calendar are opt-in integrations. Keys and OAuth files are supplied locally through `.env` and `credentials.json`; they are excluded from Git and the release ZIP. `src/server.py` is an independent Gemini HTTP backend with bearer-token protection and a localhost-only default.

Architecture diagrams are in `docs/diagrams/`.
