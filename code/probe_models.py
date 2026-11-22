"""Find the first Gemini model that works on the free tier for this key (one tiny call per model).
Prints the model name; used by the GitHub Actions workflow before the test run."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm import GeminiLLM, get_api_keys  # noqa: E402

CANDIDATES = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3-flash-preview", "gemini-2.5-flash"]

for model in CANDIDATES:
    try:
        llm = GeminiLLM(get_api_keys(), model=model, max_retries=1)
        out = llm.generate("probe", "Return only valid JSON.", 'Return {"ok": true}', temperature=0, json_mode=True)
        if "ok" in out:
            print(model)
            sys.exit(0)
    except Exception as e:
        print(f"{model}: {str(e)[:160]}", file=sys.stderr)
sys.exit("No working model found")
