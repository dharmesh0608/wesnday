# Wensday User Manual

## Start the Desktop App

Install `requirements-desktop.txt`, copy `.env.example` to `.env`, and run `python src/main.py`. If a microphone or speech dependency is unavailable, enter commands in the text box.

## Commands

- Set an alarm: “Set an alarm for 7 AM”
- List or cancel alarms: “List my alarms”; “Cancel alarm” (when only one exists)
- Save or read notes: “Note buy milk”; “Show my notes”
- Open a supported target: “Open Chrome”, “Open Google”, or “Open YouTube”
- Start a phone handoff: “Call +15551234567”
- Start a message handoff: “Send SMS to +15551234567: I am on my way”
- Read Calendar events: “Show my calendar” (after configuring Google OAuth)
- Ask a general question: configure `OPENAI_API_KEY` in `.env`

Call and message commands open a review screen in the operating system. They do not call or send automatically. Named contacts are not available yet.

## Optional Wake Word

Set `PICOVOICE_ACCESS_KEY`, add your custom Porcupine `wensday.ppn` model under `src/assets/`, and use the Wake word button. Keep the app open; background wake-word listening is not included.

## Android APK

The Kivy starter supports notes, alarms while the app is open, Google/YouTube links, and dialer/SMS handoffs. Enter `commands` in the app to see supported commands. Review and confirm calls and messages in the Android system app.

To get a debug APK, run **Build Wensday Android APK** from the GitHub Actions tab and download its `wensday-debug-apk` artifact. This starter does not include microphone input, AI, Google Calendar, background alarms, or the full desktop command set.

## Troubleshooting

- Microphone: check Windows microphone permissions and install PyAudio for the active Python version.
- Text-to-speech: check that the operating system's speech engine is available to `pyttsx3`.
- Calendar: verify `credentials.json` exists and Calendar API is enabled in the Google Cloud project.
- AI answers: verify `OPENAI_API_KEY` and network access; local commands continue to work without it.
