"""Thin wrapper around the Gemini API (google-genai SDK) with retry and a call log."""

import json
import os
import re
import time

DEFAULT_MODEL = "gemini-2.5-flash-lite"


def get_api_key():
    """Read the key from the environment. Never hard-code it in this repo."""
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def get_api_keys():
    """Main key plus optional backup keys (another team member's project) for long test runs."""
    names = ("GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3")
    return [os.environ[n] for n in names if os.environ.get(n)]


class GeminiLLM:
    def __init__(self, api_key, model=DEFAULT_MODEL, min_interval=0.0, max_retries=5):
        from google import genai  # imported here so the rest of the code works without the SDK
        from google.genai import types

        keys = [api_key] if isinstance(api_key, str) else list(api_key or [])
        if not keys:
            raise ValueError("No Gemini API key. Set GEMINI_API_KEY.")
        # v1beta: the stable v1 endpoint rejects system instructions ("Developer instruction is not enabled")
        self._clients = [genai.Client(api_key=k, http_options=types.HttpOptions(api_version="v1beta")) for k in keys]
        self._key_index = 0
        self.client = self._clients[0]
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
                    if self._key_index + 1 < len(self._clients):  # daily quota is per project: try the backup key
                        self._key_index += 1
                        self.client = self._clients[self._key_index]
                        continue
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
