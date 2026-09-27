"""Google Calendar OAuth integration (credentials.json is user-provided)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path


SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def upcoming_events(limit: int = 8) -> list[str]:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    credentials_path = Path(os.environ.get("GOOGLE_CREDENTIALS_FILE", PROJECT_ROOT / "credentials.json"))
    token_path = Path(os.environ.get("GOOGLE_TOKEN_FILE", PROJECT_ROOT / ".calendar-token.json"))
    credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES) if token_path.exists() else None

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        credentials = flow.run_local_server(port=0)
        token_path.write_text(credentials.to_json(), encoding="utf-8")

    service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
    result = service.events().list(
        calendarId="primary",
        timeMin=datetime.now(timezone.utc).isoformat(),
        maxResults=limit,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    events = []
    for event in result.get("items", []):
        start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", ""))
        events.append(f"{start}: {event.get('summary', '(untitled event)')}")
    return events