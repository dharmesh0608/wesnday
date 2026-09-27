# Developer Guide

## Local Development

Use Python 3.10 or newer. Create a virtual environment, install `requirements-desktop.txt`, copy `.env.example` to `.env`, and start the desktop app with `python src/main.py`.

Check Python syntax without starting the UI or connecting to external services:

```powershell
python -m compileall -q src
```

## Add a Command

1. Add an intent name and representative utterances to `src/intents.json`.
2. Add entity extraction for that intent in `Assistant.extract_entities` in `src/assistant.py` when it needs structured values.
3. Register the implementation in `src/actions.py` with `@action("intent_name")`.
4. Return a mapping with `status` and `say`; optional `notes`, `alarms`, or `events` fields are rendered by the desktop UI.
5. Add or update the command documentation and diagrams when behavior changes.

Keep device actions explicit. Calls and texts should go through operating-system review screens; never send them silently. Keep all keys and OAuth files in local environment/config files, not source code.

## Integrations

- OpenAI uses the Responses API in `src/ai.py`. Configure `OPENAI_API_KEY`; the SDK is imported only when an API key is present.
- Porcupine is wrapped by `src/wake_word.py`. A user-generated keyword model belongs at `src/assets/wensday.ppn` and is deliberately not distributed.
- Google Calendar OAuth is isolated in `src/calendar_service.py`. Use a desktop OAuth client and keep `credentials.json` and `.calendar-token.json` local.
- `src/server.py` is a separate Gemini-backed development HTTP service, not required by the desktop app.

## Data and Boundaries

Alarm data is stored in SQLite and notes in JSON under `src/data/`. These files are generated at runtime and should not be committed.