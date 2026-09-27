# Wensday v2

Wensday is a modular PyQt5 personal assistant for desktop. It supports text commands, optional speech input/output, persistent notes and alarms, app/web launching, optional OpenAI answers, optional Porcupine wake-word detection, Google Calendar OAuth, and phone/SMS handoffs.

## Desktop Setup

Use Python 3.10 or newer. In PowerShell from this folder:

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-desktop.txt
Copy-Item .env.example .env
python src\main.py
```

Speech recognition needs a microphone and working PyAudio installation. The app still starts if speech packages or devices are unavailable; use the text box.

## Optional Services

- OpenAI: set `OPENAI_API_KEY` in `.env`; `OPENAI_MODEL` defaults to `gpt-4.1-mini`.
- Wake word: set `PICOVOICE_ACCESS_KEY` and place your custom Porcupine keyword model at `src/assets/wensday.ppn`. Create the `.ppn` model in Picovoice Console; the model is not included.
- Google Calendar: enable the Calendar API, create desktop OAuth credentials, place `credentials.json` in the project root, then say “show my calendar.” The first request opens Google's consent flow. OAuth tokens stay local and are ignored by Git.
- Calls and SMS: provide a phone number. Wensday opens the device's dialer or message composer for review; it does not place calls or send messages automatically. Contact-name lookup is not configured.

## Shared Gemini Server

`src/server.py` is a separate optional Gemini-backed HTTP service. Set `GEMINI_API_KEY` and a private `WENSDAY_SERVER_TOKEN`, then run `python src/server.py`. It binds to localhost by default. Only use `WENSDAY_HOST=0.0.0.0` on a trusted LAN; do not expose this plain-HTTP development server to the public internet.

## Project Layout

- `src/`: desktop assistant, actions, speech, AI and integrations
- `docs/`: user manual, developer guide, architecture notes and diagrams

User-provided API keys, OAuth credentials, OAuth tokens, wake-word models, and runtime data are excluded from version control and the ZIP bundle.
