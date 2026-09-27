"""Optional OpenAI Responses API fallback."""

from __future__ import annotations

import os


class AIUnavailableError(Exception):
    pass


def answer(message: str) -> str | None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise AIUnavailableError("Install the optional OpenAI package to enable AI answers.") from exc

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
        instructions=(
            "You are Wensday, a concise personal assistant. You cannot access or control "
            "the user's device; never claim that you performed an action on it."
        ),
        input=message,
    )
    text = response.output_text.strip()
    return text or None