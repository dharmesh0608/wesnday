# Wensday v2

Wensday is a modular personal assistant with a PyQt5 desktop app and a separate Kivy Android starter. The desktop app includes optional speech, AI, wake-word, and Calendar integrations. The Android app is an independent client for notes, foreground alarms, web links, and reviewed dialer/SMS handoffs.

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

## Android APK

The Android client is separate from the PyQt5 desktop app and does not have desktop feature parity. It stores notes and alarms locally; alarm alerts require Wensday to remain open. Calls and SMS open native review screens and are never sent automatically.

To build an APK, push this project to a GitHub repository with Actions enabled, then open **Actions**, select **Build Android APK**, and choose **Run workflow**. Download the `wensday-debug-apk` artifact after the job completes. The workflow builds a debug APK, not a signed Play Store release.

Local Buildozer builds are best run from Linux or WSL. The project includes `buildozer.spec` and `requirements-android.txt` for that target.

## Project Layout

- `src/`: desktop assistant, actions, speech, AI and integrations
- `android/`: standalone Kivy mobile client
- `.github/workflows/android-apk.yml`: GitHub Actions debug APK build
- `docs/`: user manual, developer guide, architecture notes and diagrams

User-provided API keys, OAuth credentials, OAuth tokens, wake-word models, and runtime data are excluded from version control and the ZIP bundle.
