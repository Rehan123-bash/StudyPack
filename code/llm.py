"""Thin wrapper around the Gemini API (google-genai SDK) with retry and a call log."""

import json
import os
import re
import time

DEFAULT_MODEL = "gemini-2.5-flash"


def get_api_key():
    """Read the key from the environment. Never hard-code it in this repo."""
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


class GeminiLLM:
    def __init__(self, api_key, model=DEFAULT_MODEL, min_interval=0.0, max_retries=5):
        from google import genai  # imported here so the rest of the code works without the SDK

        if not api_key:
            raise ValueError("No Gemini API key. Set GEMINI_API_KEY.")
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.min_interval = min_interval  # seconds between calls, to stay under the free-tier RPM
        self.max_retries = max_retries
        self._last_call = 0.0
        self.calls = []  # one entry per API call: prompt id, seconds, tokens

    def generate(self, prompt_id, system, user, temperature=None, json_mode=True):
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system or None,
            temperature=temperature,
            response_mime_type="application/json" if json_mode else "text/plain",
        )
        delay = 10.0
        for attempt in range(self.max_retries + 1):
            wait = self.min_interval - (time.time() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            start = time.time()
            self._last_call = start
            try:
                resp = self.client.models.generate_content(
                    model=self.model, contents=user, config=config
                )
                text = resp.text or ""
                usage = getattr(resp, "usage_metadata", None)
                self.calls.append(
                    {
                        "prompt_id": prompt_id,
                        "model": self.model,
                        "seconds": round(time.time() - start, 2),
                        "input_tokens": getattr(usage, "prompt_token_count", None),
                        "output_tokens": getattr(usage, "candidates_token_count", None),
                    }
                )
                return text
            except Exception as e:  # rate limit or temporary server error -> wait and retry
                msg = str(e)
                retryable = any(s in msg for s in ("429", "RESOURCE_EXHAUSTED", "500", "503", "UNAVAILABLE", "DEADLINE"))
                if not retryable or attempt == self.max_retries:
                    raise
                if "per day" in msg.lower() or "PerDay" in msg:
                    raise RuntimeError(
                        "Daily free-tier quota used up for this model. Try another model "
                        "(e.g. gemini-2.5-flash-lite) or another team member's API key."
                    ) from e
                time.sleep(delay)
                delay = min(delay * 2, 90)


def parse_json(text):
    """Return (data, strict_ok). strict_ok is False if the reply needed repair to parse."""
    try:
        return json.loads(text), True
    except Exception:
        pass
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    match = re.search(r"\{.*\}", cleaned, re.S)
    if match:
        try:
            return json.loads(match.group(0)), False
        except Exception:
            pass
    return None, False
