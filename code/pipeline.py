"""StudyPack prompt workflow.

run_final()  -> the final 4-step chain (v3) used by the app:
    P1 concept extractor -> P2 summary + key terms -> P3 question generator -> P4 verifier
    plus code checks: empty-input check, exact-quote check, gap flags.
run_v1(), run_v2() -> older prompt versions, kept so the test runner can compare versions.
run_judge()  -> evaluation prompt E1 (testing only).
"""

import json
import re
from pathlib import Path

from llm import parse_json

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"

MAX_CHARS = 60000  # about 15k tokens; longer notes should be split by topic
MIN_CHARS = 40
MAX_TERMS = 10

# Settings shown in the app -> values passed into the prompts
FORMATS = {"Mixed": "mixed", "MCQ": "mcq", "Short answer": "short", "Flashcards": "flashcard"}
DIFFICULTIES = {"Mixed": "mixed", "Easy (recall)": "easy", "Challenging (apply/analyze)": "challenging"}
TEMPERATURES = {"P1": 0.2, "P2": 0.3, "P3": 0.4, "P4": 0.0, "E1": 0.0, "v2_P1": 0.2, "v2_P2": 0.3, "v2_P3": 0.4}
HIGHER_ORDER = {"apply", "analyze", "analyse", "evaluate", "create"}


# ---------- prompt files ----------

def load_prompt(rel_path):
    """Prompt files have '### SYSTEM' and '### USER' sections; '#' lines above them are comments."""
    text = (PROMPTS / rel_path).read_text(encoding="utf-8")
    system = text.split("### SYSTEM", 1)[1].split("### USER", 1)[0].strip()
    user = text.split("### USER", 1)[1].strip()
    if system.lower() == "(none)":
        system = ""
    return system, user


def fill(template, **values):
    # Plain replace (not str.format) because the prompts contain JSON braces.
    for key, value in values.items():
        template = template.replace("{" + key + "}", str(value))
    return template


# ---------- notes helpers ----------

def number_lines(notes):
    """Put 'L<n>: ' before every non-empty line so prompts can cite line numbers."""
    lines = [ln.rstrip() for ln in notes.splitlines() if ln.strip()]
    numbered = "\n".join(f"L{i}: {ln}" for i, ln in enumerate(lines, 1))
    return numbered, lines


def _norm(text):
    text = text.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"[–—]", "-", text)
    text = re.sub(r"[^\w\s'\-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def quote_in_notes(quote, notes):
    """Code check (not the model): is the source quote really in the notes? Ignores case/punctuation/spacing."""
    q = _norm(quote or "")
    joined = re.sub(r"(\w)-[ \t]*\n\s*(\w)", r"\1\2", notes)  # re-join words split across lines ("ar-\nrives")
    return len(q.split()) >= 3 and (q in _norm(notes) or q in _norm(joined))


def check_input(notes):
    """Return an error message, or None if the notes can be sent to the model."""
    text = (notes or "").strip()
    if len(text) < MIN_CHARS or not re.search(r"[A-Za-zऀ-ॿ]{3,}", text):
        return "No notes found. Paste or upload at least a few lines of lecture notes."
    if len(text) > MAX_CHARS:
        return f"These notes are too long ({len(text):,} characters). Split them by topic (max {MAX_CHARS:,})."
    return None


LIST_KEYS = {"P1": "concepts", "P2": "key_terms", "P3": "questions", "P4": "checks",
             "v2_P1": "concepts", "v2_P2": "key_terms", "v2_P3": "questions"}


def _dicts(items):
    """Keep only dict items (the model sometimes returns a bare string inside a list)."""
    return [x for x in (items or []) if isinstance(x, dict)]


def _call_json(llm, prompt_id, system, user, log):
    raw = llm.generate(prompt_id, system, user, temperature=TEMPERATURES.get(prompt_id), json_mode=True)
    data, strict = parse_json(raw)
    # The model sometimes wraps the object in a list ([{...}]) or returns only the list. Repair it, but
    # record the step as not strictly valid so the test results show it.
    if isinstance(data, list):
        strict = False
        if len(data) == 1 and isinstance(data[0], dict) and LIST_KEYS.get(prompt_id, "") in data[0]:
            data = data[0]
        else:
            data = {LIST_KEYS.get(prompt_id, "items"): data}
    log.append({"step": prompt_id, "json_valid": strict, "parsed": isinstance(data, dict)})
    if not isinstance(data, dict):
        raise ValueError(f"{prompt_id} did not return a JSON object. Raw reply starts: {raw[:200]!r}")
    return data


# ---------- final workflow (v3) ----------

def run_final(notes, llm, num_questions=8, question_format="mixed", difficulty="mixed", progress=None):
    """Return a study pack dict. progress(step_no, message) is an optional callback for the UI."""
    say = progress or (lambda step, msg: None)
    log = []

    error = check_input(notes)
    if error:
        return {"status": "rejected", "reason": error, "api_calls": 0, "log": log}

    numbered, lines = number_lines(notes)

    say(1, "Step 1/4: Finding the concepts in your notes")
    sys1, usr1 = load_prompt("final/P1_concept_extractor.txt")
    s1 = _call_json(llm, "P1", sys1, fill(usr1, numbered_notes=numbered), log)
    if not s1.get("is_lecture_notes", True):
        return {"status": "rejected", "reason": s1.get("reason") or "This does not look like lecture notes.",
                "api_calls": 1, "log": log, "steps": {"P1": s1}}

    concepts = _dicts(s1.get("concepts"))
    explained = [c for c in concepts if c.get("coverage") == "explained"]
    gaps = [
        {"concept": c.get("name", ""), "lines": c.get("lines", [])}
        for c in concepts if c.get("coverage") == "mentioned_only"
    ]
    concepts_json = json.dumps(concepts, ensure_ascii=False)

    say(2, "Step 2/4: Writing the summary and key terms")
    sys2, usr2 = load_prompt("final/P2_summary_terms.txt")
    s2 = _call_json(llm, "P2", sys2, fill(usr2, numbered_notes=numbered, concepts_json=concepts_json,
                                           max_terms=MAX_TERMS), log)

    questions, note, checks = [], "", {}
    steps = {"P1": s1, "P2": s2}
    calls = 2
    if explained:
        say(3, "Step 3/4: Writing practice questions")
        sys3, usr3 = load_prompt("final/P3_question_generator.txt")
        s3 = _call_json(llm, "P3", sys3, fill(usr3, numbered_notes=numbered, concepts_json=concepts_json,
                                               num_questions=num_questions, question_format=question_format,
                                               difficulty=difficulty), log)
        questions = _dicts(s3.get("questions"))
        note = s3.get("note", "") or ""
        steps["P3"] = json.loads(json.dumps(s3))  # raw copy before code adds fields
        calls = 3
        for i, q in enumerate(questions, 1):
            q["id"] = q.get("id") or f"Q{i}"
            q["quote_found"] = quote_in_notes(q.get("source_quote", ""), notes)

        if questions:
            say(4, "Step 4/4: Checking every answer against your notes")
            sys4, usr4 = load_prompt("final/P4_verifier.txt")
            slim = [{k: q.get(k) for k in ("id", "type", "question", "options", "answer", "source_lines")}
                    for q in questions]
            s4 = _call_json(llm, "P4", sys4, fill(usr4, numbered_notes=numbered,
                                                   questions_json=json.dumps(slim, ensure_ascii=False)), log)
            checks = {c.get("id"): c for c in _dicts(s4.get("checks"))}
            steps["P4"] = s4
            calls = 4
    else:
        note = "Your notes only mention topics without explaining them, so no questions were written."

    verified, removed = [], []
    for q in questions:
        c = checks.get(q["id"], {})
        q["verdict"] = c.get("verdict", "NOT CHECKED")
        q["verdict_reason"] = c.get("reason", "")
        if q["verdict"] == "SUPPORTED" and q["quote_found"]:
            verified.append(q)
        else:
            why = []
            if q["verdict"] != "SUPPORTED":
                why.append(f"checker said {q['verdict']}: {q['verdict_reason']}".strip(": "))
            if not q["quote_found"]:
                why.append("source quote not found in the notes")
            q["removed_because"] = "; ".join(why)
            removed.append(q)

    return {
        "status": "ok",
        "topic": s1.get("topic", ""),
        "languages": s1.get("languages", []),
        "concepts": concepts,
        "summary": s2.get("summary", ""),
        "key_terms": _dicts(s2.get("key_terms")),
        "questions": verified,
        "removed": removed,
        "gaps": gaps,
        "note": note,
        "settings": {"num_questions": num_questions, "question_format": question_format, "difficulty": difficulty},
        "stats": {
            "generated": len(questions),
            "verified": len(verified),
            "removed": len(removed),
            "quote_found": sum(1 for q in questions if q["quote_found"]),
            "line_count": len(lines),
        },
        "api_calls": calls,
        "log": log,
        "steps": steps,  # raw output of each prompt, kept as evidence for the prompt sheets
    }


# ---------- older versions (for comparison in testing) ----------

def run_v1(notes, llm):
    _, usr = load_prompt("v1/P0_single_prompt.txt")
    raw = llm.generate("v1_P0", "", fill(usr, notes=notes), temperature=None, json_mode=False)
    return {"status": "ok", "raw_text": raw, "api_calls": 1}


def run_v2(notes, llm, num_questions=8, question_format="mixed"):
    log = []
    s1p, u1 = load_prompt("v2/P1_concepts_v2.txt")
    s1 = _call_json(llm, "v2_P1", s1p, fill(u1, notes=notes), log)
    concepts_json = json.dumps(s1.get("concepts", []), ensure_ascii=False)
    s2p, u2 = load_prompt("v2/P2_summary_terms_v2.txt")
    s2 = _call_json(llm, "v2_P2", s2p, fill(u2, notes=notes, concepts_json=concepts_json), log)
    s3p, u3 = load_prompt("v2/P3_questions_v2.txt")
    s3 = _call_json(llm, "v2_P3", s3p, fill(u3, notes=notes, concepts_json=concepts_json,
                                             num_questions=num_questions, question_format=question_format), log)
    return {"status": "ok", "topic": s1.get("topic", ""), "summary": s2.get("summary", ""),
            "key_terms": s2.get("key_terms", []) or [], "questions": s3.get("questions", []) or [],
            "api_calls": 3, "log": log}


# ---------- rendering + evaluation ----------

def render_pack_text(pack):
    """Plain-text view of a pack (same layout for every version, so the judge compares fairly)."""
    if "raw_text" in pack:
        return pack["raw_text"]
    out = ["SUMMARY", pack.get("summary", ""), "", "KEY TERMS"]
    for t in pack.get("key_terms", []):
        out.append(f"- {t.get('term', '')}: {t.get('definition', '')}")
    out += ["", "PRACTICE QUESTIONS"]
    for i, q in enumerate(pack.get("questions", []), 1):
        out.append(f"Q{i}. {q.get('question', '')}")
        for opt in q.get("options") or []:
            out.append(f"   {opt}")
        out.append(f"   Answer: {q.get('answer', '')}")
    return "\n".join(out)


def render_markdown(pack):
    """Downloadable study pack for students."""
    md = [f"# Study pack: {pack.get('topic', '')}", "", "## Summary", pack.get("summary", ""), "", "## Key terms"]
    for t in pack.get("key_terms", []):
        md.append(f"- **{t.get('term', '')}**: {t.get('definition', '')}")
    md += ["", "## Practice questions"]
    for i, q in enumerate(pack.get("questions", []), 1):
        md.append(f"**Q{i} ({q.get('bloom_level', '')}).** {q.get('question', '')}")
        for opt in q.get("options") or []:
            md.append(f"- {opt}")
        lines = ", ".join(str(x) for x in q.get("source_lines", []))
        md.append(f"> Answer: {q.get('answer', '')}  \n> Source: line {lines}: \"{q.get('source_quote', '')}\"")
        md.append("")
    if pack.get("gaps"):
        md += ["## Gaps in your notes"]
        for g in pack["gaps"]:
            md.append(f"- {g['concept']} is mentioned but never explained (line {', '.join(map(str, g['lines']))}).")
    return "\n".join(md)


def run_judge(notes, pack, llm):
    sysj, usrj = load_prompt("eval/E1_judge.txt")
    raw = llm.generate("E1", sysj, fill(usrj, notes=notes, pack_text=render_pack_text(pack)),
                       temperature=TEMPERATURES["E1"], json_mode=True)
    data, _ = parse_json(raw)
    if isinstance(data, list):  # same repair as the main chain
        data = data[0] if len(data) == 1 and isinstance(data[0], dict) and "questions" in data[0] else {"questions": data}
    return data or {"questions": [], "outside_statements": None, "error": "judge returned no JSON"}


def judge_metrics(judgement):
    qs = _dicts(judgement.get("questions"))
    n = len(qs)
    yes = sum(1 for q in qs if str(q.get("supported", "")).lower() == "yes")
    higher = sum(1 for q in qs if str(q.get("bloom_level", "")).lower() in HIGHER_ORDER)
    return {"judged_questions": n, "supported_yes": yes, "higher_order": higher,
            "outside_statements": judgement.get("outside_statements")}
