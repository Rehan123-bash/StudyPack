"""Run the StudyPack test set against the real Gemini API and write the tables used in the report.

Usage (from the repo root, with GEMINI_API_KEY set):
    python code/run_tests.py                      # all 14 test cases + v1/v2/v3 comparison
    python code/run_tests.py --model gemini-2.5-flash-lite
    python code/run_tests.py --cases 1,2,3        # only some cases
    python code/run_tests.py --fresh              # ignore saved outputs and call the API again

Outputs (test-data/outputs/):
    v1/, v2/, v3/   raw output of every run, one JSON per test case (v3 = final workflow)
    judge/          evaluation-judge (E1) results used for the version comparison
    test_table.md / .csv          the Section 4 test table
    iteration_metrics.md / .csv   numbers for the Section 3 prompt iteration log
    run_info.json                 model, date, number of API calls, tokens
Saved outputs are reused on the next run, so if you hit a rate limit just run the command again.
"""

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline  # noqa: E402
from llm import DEFAULT_MODEL, GeminiLLM, get_api_key  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "test-data"
OUT = DATA / "outputs"

HINGLISH = {"hai", "hain", "ka", "ki", "ke", "ko", "mein", "se", "jo", "ye", "yeh", "hota", "hoti", "hote", "karta",
            "karti", "karna", "karni", "padta", "padti", "banta", "liye", "isliye", "kyunki", "sirf", "aur", "bhi",
            "lekin", "jaise", "nahi", "ek", "wala", "wali", "jude", "kuch", "tarah", "bilkul", "usi", "poori"}


# ---------- helpers ----------

def generated_text(pack):
    """All text the model wrote for the student (not the copied source quotes)."""
    parts = [pack.get("summary", "")]
    for t in pack.get("key_terms", []):
        parts += [t.get("term", ""), t.get("definition", "")]
    for q in pack.get("questions", []):
        parts += [q.get("question", ""), q.get("answer", "")] + [str(o) for o in (q.get("options") or [])]
    return " ".join(parts)


def higher_order_count(pack):
    return sum(1 for q in pack.get("questions", []) if str(q.get("bloom_level", "")).lower() in pipeline.HIGHER_ORDER)


def run_check(chk, pack):
    """Return (passed, detail)."""
    kind, val = chk["check"], chk["value"]
    stats = pack.get("stats", {})
    qs = pack.get("questions", [])
    if kind == "status":
        return pack.get("status") == val, f"status={pack.get('status')}"
    if pack.get("status") != "ok" and kind != "api_calls_max":
        return False, "no pack produced"
    if kind == "api_calls_max":
        return pack.get("api_calls", 99) <= val, f"API calls={pack.get('api_calls')}"
    if kind == "summary_max_words":
        n = len(pack.get("summary", "").split())
        return n <= val, f"summary {n} words"
    if kind == "min_key_terms":
        n = len(pack.get("key_terms", []))
        return n >= val, f"{n} key terms"
    if kind == "min_verified":
        return len(qs) >= val, f"{len(qs)} verified"
    if kind == "max_verified":
        return len(qs) <= val, f"{len(qs)} verified"
    if kind == "min_higher_order":
        n = higher_order_count(pack)
        return n >= val, f"{n} Apply/Analyze"
    if kind == "quote_rate_min":
        gen = stats.get("generated", 0)
        rate = stats.get("quote_found", 0) / gen if gen else 0.0
        return rate >= val, f"quotes found {stats.get('quote_found', 0)}/{gen}"
    if kind == "all_type":
        ok = bool(qs) and all(str(q.get("type", "")).lower() == val for q in qs)
        if val == "mcq":
            ok = ok and all(len(q.get("options") or []) == 4 for q in qs)
        return ok, f"types={sorted({str(q.get('type')) for q in qs})}"
    if kind == "min_gaps":
        n = len(pack.get("gaps", []))
        return n >= val, f"{n} gap flags"
    if kind == "not_contains":
        text = generated_text(pack).lower()
        hits = [w for w in val if re.search(rf"\b{w}\b", text)]
        return not hits, f"found {hits}" if hits else "none found"
    if kind == "english_output":
        words = re.findall(r"[a-z]+", generated_text(pack).lower())
        ratio = sum(1 for w in words if w in HINGLISH) / max(len(words), 1)
        return ratio <= val, f"Hindi-word ratio {ratio:.1%}"
    return False, f"unknown check {kind}"


def short_actual(pack):
    if pack.get("status") == "error":
        return f"Error: {pack.get('error', '')[:80]}"
    if pack.get("status") == "rejected":
        return f"Rejected after {pack.get('api_calls', 0)} API call(s): {pack.get('reason', '')[:90]}"
    s = pack.get("stats", {})
    bits = [f"{s.get('verified', 0)} Qs verified ({s.get('removed', 0)} removed)",
            f"{higher_order_count(pack)} Apply/Analyze",
            f"{len(pack.get('key_terms', []))} terms",
            f"summary {len(pack.get('summary', '').split())} words"]
    if pack.get("gaps"):
        bits.append(f"{len(pack['gaps'])} gap flags")
    if s.get("generated"):
        bits.append(f"quotes found {s.get('quote_found', 0)}/{s.get('generated', 0)}")
    return "; ".join(bits)


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def cached_run(path, fresh, fn, llm):
    if path.exists() and not fresh:
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved.get("status") != "error":  # errors (e.g. a broken earlier run) are retried
            return saved
    before = len(llm.calls)
    try:
        result = fn()
    except RuntimeError as e:  # daily quota: stop everything
        if "Daily free-tier quota" in str(e):
            print(f"\nSTOPPED: {e}\nSaved results so far are kept. Run again later or with --model.")
            sys.exit(2)
        result = {"status": "error", "error": str(e)}
    except Exception as e:
        result = {"status": "error", "error": f"{type(e).__name__}: {e}"}
    result["calls"] = llm.calls[before:]
    result["run_at"] = dt.datetime.now().isoformat(timespec="seconds")
    save(path, result)
    return result


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in r) + " |")
    return "\n".join(out)


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--cases", default="all", help="'all' or comma-separated test numbers, e.g. 1,2,3")
    ap.add_argument("--versions", default="v1,v2,v3")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--fresh", action="store_true", help="ignore saved outputs and call the API again")
    ap.add_argument("--interval", type=float, default=7.0, help="seconds between API calls (free tier ~10/min)")
    args = ap.parse_args()

    key = get_api_key()
    if not key:
        sys.exit("Set GEMINI_API_KEY first (see README).")
    llm = GeminiLLM(key, model=args.model, min_interval=args.interval)

    cases = json.loads((DATA / "test_cases.json").read_text(encoding="utf-8"))
    if args.cases != "all":
        wanted = {int(x) for x in args.cases.split(",")}
        cases = [c for c in cases if c["no"] in wanted]
    versions = args.versions.split(",")

    rows, metrics = [], {v: [] for v in ("v1", "v2", "v3")}
    for c in cases:
        notes = (DATA / "inputs" / c["input_file"]).read_text(encoding="utf-8")
        st = c["settings"]
        tag = Path(c["input_file"]).stem
        print(f"Test {c['no']:>2} [{c['type']}] {c['short']}")

        # final workflow (v3) on every case -> test table
        pack = cached_run(OUT / "v3" / f"{tag}.json", args.fresh,
                          lambda: pipeline.run_final(notes, llm, **st), llm)
        results = [run_check(chk, pack) for chk in c["checks"]]
        passed = all(ok for ok, _ in results)
        failed_detail = "; ".join(d for ok, d in results if not ok)
        rows.append([c["no"], c["short"], c["type"], c["expected"], short_actual(pack),
                     "Pass" if passed else "Fail", failed_detail])
        print(f"      -> {'PASS' if passed else 'FAIL'}  {short_actual(pack)}")

        # version comparison on the normal cases
        if c.get("compare"):
            runs = {"v3": pack}
            if "v1" in versions:
                runs["v1"] = cached_run(OUT / "v1" / f"{tag}.json", args.fresh, lambda: pipeline.run_v1(notes, llm), llm)
            if "v2" in versions:
                runs["v2"] = cached_run(OUT / "v2" / f"{tag}.json", args.fresh,
                                        lambda: pipeline.run_v2(notes, llm, st["num_questions"], st["question_format"]), llm)
            for v, p in runs.items():
                if v not in versions:
                    continue
                entry = {"case": c["no"], "pack": p}
                if not args.no_judge and p.get("status") == "ok":
                    entry["judge"] = cached_run(OUT / "judge" / f"{v}_{tag}.json", args.fresh,
                                                lambda p=p: pipeline.run_judge(notes, p, llm), llm)
                metrics[v].append(entry)

    # ---- test table ----
    headers = ["Test no.", "Input (short)", "Type", "Expected output", "Actual output (short)", "Pass / Fail", "Why it failed"]
    with open(OUT / "test_table.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([headers] + rows)
    n_pass = sum(1 for r in rows if r[5] == "Pass")
    (OUT / "test_table.md").write_text(
        f"# Test table ({n_pass}/{len(rows)} passed, model {args.model})\n\n" + md_table(headers, rows) + "\n",
        encoding="utf-8")

    # ---- iteration metrics ----
    mrows = []
    for v in ("v1", "v2", "v3"):
        entries = metrics[v]
        if not entries:
            continue
        packs = [e["pack"] for e in entries]
        ok_packs = [p for p in packs if p.get("status") == "ok"]
        steps = [s for p in ok_packs for s in p.get("log", [])]
        json_valid = "n/a (plain text)" if v == "v1" else f"{sum(s['json_valid'] for s in steps)}/{len(steps)} steps"
        judged = [pipeline.judge_metrics(e["judge"]) for e in entries if "judge" in e]
        jq = sum(j["judged_questions"] for j in judged)
        yes = sum(j["supported_yes"] for j in judged)
        hi = sum(j["higher_order"] for j in judged)
        outside = sum(j["outside_statements"] or 0 for j in judged)
        if v == "v3":
            linked = sum(sum(1 for q in p.get("questions", []) if q.get("quote_found")) for p in ok_packs)
            gen = sum(p.get("stats", {}).get("generated", 0) for p in ok_packs)
            removed = sum(p.get("stats", {}).get("removed", 0) for p in ok_packs)
            extra = f"{removed} of {gen} generated questions removed by checker"
        else:
            linked, extra = 0, ""
        calls = [cl for p in packs for cl in p.get("calls", [])]
        secs = sum(cl.get("seconds") or 0 for cl in calls) / max(len(packs), 1)
        mrows.append([v, len(packs), len(ok_packs), json_valid, jq,
                      f"{yes}/{jq} ({yes / jq:.0%})" if jq else "-",
                      f"{hi}/{jq} ({hi / jq:.0%})" if jq else "-",
                      outside, f"{linked}/{jq}" if jq else "-", f"{secs:.1f}", extra])
    mheaders = ["Version", "Test cases", "Runs OK", "Valid JSON", "Questions shown to student",
                "Supported by notes (judge)", "Apply/Analyze or higher (judge)", "Outside facts in summary/terms (judge)",
                "Questions with verified source link", "Avg seconds per pack", "Notes"]
    with open(OUT / "iteration_metrics.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([mheaders] + mrows)
    (OUT / "iteration_metrics.md").write_text(
        f"# Prompt version comparison (normal test cases 1-7, model {args.model})\n\n" + md_table(mheaders, mrows) + "\n",
        encoding="utf-8")

    all_calls = []
    for f in OUT.rglob("*.json"):
        if f.name != "run_info.json":
            try:
                all_calls += json.loads(f.read_text(encoding="utf-8")).get("calls", [])
            except Exception:
                pass
    save(OUT / "run_info.json", {
        "model": args.model, "finished_at": dt.datetime.now().isoformat(timespec="seconds"),
        "test_cases": len(rows), "passed": n_pass, "api_calls_total": len(all_calls),
        "input_tokens_total": sum(c.get("input_tokens") or 0 for c in all_calls),
        "output_tokens_total": sum(c.get("output_tokens") or 0 for c in all_calls),
    })
    print(f"\nDone: {n_pass}/{len(rows)} tests passed. Tables written to {OUT}")


if __name__ == "__main__":
    main()
