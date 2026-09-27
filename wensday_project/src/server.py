"""Small shared Gemini backend for Wensday PC and mobile clients.

Required environment variables:
    GEMINI_API_KEY       Replacement key from Google AI Studio (never commit it).
    WENSDAY_SERVER_TOKEN Random private token shared with trusted clients.

Run locally with: python server.py
For phone access on the same trusted Wi-Fi, set WENSDAY_HOST=0.0.0.0 and use
this computer's LAN IP in WENSDAY_SERVER_URL on the phone. Do not expose this
plain-HTTP development server directly to the public internet; use HTTPS and
proper per-user authentication for a hosted app.
"""

from __future__ import annotations

import hmac
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

MAX_BODY_BYTES = 8192
SYSTEM_INSTRUCTION = (
    "You are Wensday, a helpful assistant. Answer clearly and concisely. "
    "You cannot execute commands on a user's PC or phone. Never claim that "
    "you performed an action on a device."
)


class GeminiError(Exception):
    pass


def ask_gemini(message: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise GeminiError("AI provider is not configured")

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{quote(model, safe='')}:generateContent"
    )
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [{"parts": [{"text": message}]}],
        "generationConfig": {"maxOutputTokens": 512},
    }
    request = Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise GeminiError("AI provider request failed") from exc

    try:
        parts = result["candidates"][0]["content"]["parts"]
        answer = "\n".join(part["text"] for part in parts if isinstance(part.get("text"), str))
    except (KeyError, IndexError, TypeError) as exc:
        raise GeminiError("AI provider returned an unexpected response") from exc
    if not answer.strip():
        raise GeminiError("AI provider returned an empty response")
    return answer.strip()


class WensdayHandler(BaseHTTPRequestHandler):
    server_version = "WensdayServer/1.0"

    def send_json(self, status: HTTPStatus, payload: dict[str, str]) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_json(HTTPStatus.OK, {"status": "ok"})
        else:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/api/chat":
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        expected_token = os.environ.get("WENSDAY_SERVER_TOKEN", "")
        authorization = self.headers.get("Authorization", "")
        supplied_token = authorization.removeprefix("Bearer ")
        if not expected_token or not hmac.compare_digest(supplied_token, expected_token):
            self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0
        if content_length <= 0 or content_length > MAX_BODY_BYTES:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid request size"})
            return

        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid JSON"})
            return
        message = payload.get("message") if isinstance(payload, dict) else None
        if not isinstance(message, str) or not message.strip() or len(message) > 6000:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "message must be 1-6000 characters"})
            return

        try:
            reply = ask_gemini(message.strip())
        except GeminiError:
            self.send_json(HTTPStatus.BAD_GATEWAY, {"error": "AI provider request failed"})
            return
        self.send_json(HTTPStatus.OK, {"reply": reply})

    def log_message(self, format: str, *args: object) -> None:
        # Log request metadata only; never log request bodies or authorization headers.
        print(f"{self.client_address[0]} - {format % args}")


def main() -> None:
    if not os.environ.get("WENSDAY_SERVER_TOKEN"):
        raise SystemExit("Set WENSDAY_SERVER_TOKEN before starting the server.")

    host = os.environ.get("WENSDAY_HOST", "127.0.0.1")
    port = int(os.environ.get("WENSDAY_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), WensdayHandler)
    server.daemon_threads = True
    print(f"Wensday server listening at http://{host}:{port}")
    print("Health check: /health; chat endpoint: POST /api/chat")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Wensday server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()