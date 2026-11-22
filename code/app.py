"""StudyPack web app (Streamlit). Run locally with:  streamlit run code/app.py"""

import json
import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline  # noqa: E402
from llm import DEFAULT_MODEL, GeminiLLM  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "test-data" / "inputs"
MODELS = list(dict.fromkeys([DEFAULT_MODEL, "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash"]))

st.set_page_config(page_title="StudyPack", page_icon="📚", layout="wide")


def api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        key = None
    return key or os.environ.get("GEMINI_API_KEY")


def read_upload(upload):
    if upload is None:
        return ""
    if upload.name.lower().endswith(".pdf"):
        from pypdf import PdfReader

        text = "\n".join((page.extract_text() or "") for page in PdfReader(upload).pages)
        if len(text.strip()) < 50:
            st.warning("This PDF has no text layer (it looks scanned). Scanned PDFs are not supported yet. "
                       "Paste the text instead, or use a text-based PDF.")
        return text
    return upload.read().decode("utf-8", errors="ignore")


# ---------- sidebar ----------
with st.sidebar:
    st.header("Settings")
    num_q = st.slider("Number of questions", 3, 15, 8)
    fmt = st.radio("Question format", list(pipeline.FORMATS), index=0)
    diff = st.radio("Difficulty", list(pipeline.DIFFICULTIES), index=0)
    model = st.selectbox("Model", MODELS, index=0)
    key = api_key()
    if not key:
        key = st.text_input("Gemini API key (only for running locally)", type="password")
    st.divider()
    st.caption("Use course notes only. Do not paste names, roll numbers or other personal data: on the free tier, "
               "Google may use inputs to improve its models. AI output can still be wrong, so check anything important.")

# ---------- input ----------
st.title("📚 StudyPack")
st.write("Turn lecture notes into a summary, key terms and practice questions. "
         "**Every answer is checked against your notes** and linked to the line it came from.")

samples = {"(none)": ""} | {p.stem: p.read_text(encoding="utf-8") for p in sorted(SAMPLES.glob("T*.txt"))}
tab_paste, tab_upload = st.tabs(["Paste notes", "Upload a file (.txt, .md, .pdf)"])
with tab_paste:
    sample = st.selectbox("Or try a sample from our test set", list(samples))
    pasted = st.text_area("Lecture notes", value=samples[sample], height=260,
                          placeholder="Paste the notes for one topic here...")
with tab_upload:
    upload = st.file_uploader("Notes file", type=["txt", "md", "pdf"])
notes = read_upload(upload) if upload else pasted

if st.button("Build study pack", type="primary", use_container_width=True):
    if not key:
        st.error("No API key found. Add GEMINI_API_KEY to the app secrets, or paste a key in the sidebar.")
        st.stop()
    llm = GeminiLLM(key, model=model)
    with st.status("Building your study pack...", expanded=True) as status:
        try:
            pack = pipeline.run_final(
                notes, llm, num_questions=num_q, question_format=pipeline.FORMATS[fmt],
                difficulty=pipeline.DIFFICULTIES[diff], progress=lambda step, msg: st.write(msg),
            )
        except Exception as e:
            status.update(label="Something went wrong", state="error")
            st.error(f"{type(e).__name__}: {e}")
            st.stop()
        status.update(label="Done" if pack["status"] == "ok" else "Could not build a pack",
                      state="complete" if pack["status"] == "ok" else "error", expanded=False)
    st.session_state["pack"] = pack
    st.session_state["model"] = model

# ---------- output ----------
pack = st.session_state.get("pack")
if pack:
    if pack["status"] != "ok":
        st.error(pack["reason"])
        st.stop()

    s = pack["stats"]
    st.subheader(f"Study pack: {pack.get('topic', '')}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Questions verified", s["verified"])
    c2.metric("Removed by checker", s["removed"])
    c3.metric("Key terms", len(pack["key_terms"]))
    c4.metric("Gaps flagged", len(pack["gaps"]))
    if pack.get("note"):
        st.info(pack["note"])

    t1, t2, t3, t4, t5 = st.tabs(["Summary & key terms", "Practice questions", "Gaps in your notes",
                                  "Removed by checker", "Raw JSON"])
    with t1:
        st.write(pack["summary"])
        st.markdown("#### Key terms")
        for t in pack["key_terms"]:
            lines = ", ".join(map(str, t.get("lines", [])))
            st.markdown(f"**{t.get('term', '')}**: {t.get('definition', '')}  \n:gray[line {lines}]")
    with t2:
        for i, q in enumerate(pack["questions"], 1):
            st.markdown(f"**Q{i}** · {q.get('bloom_level', '')} · {q.get('type', '')}")
            st.markdown(q.get("question", ""))
            for opt in q.get("options") or []:
                st.markdown(f"- {opt}")
            with st.expander("Show answer"):
                st.markdown(f"**Answer:** {q.get('answer', '')}")
                lines = ", ".join(map(str, q.get("source_lines", [])))
                st.markdown(f"**From your notes (line {lines}):** “{q.get('source_quote', '')}”")
                st.success("Checked: the answer is supported by your notes and the quote was found in them.")
        if not pack["questions"]:
            st.write("No questions passed the check.")
    with t3:
        if pack["gaps"]:
            st.write("These topics are named in your notes but never explained. Read them from the textbook:")
            for g in pack["gaps"]:
                st.markdown(f"- **{g['concept']}** (line {', '.join(map(str, g['lines']))})")
        else:
            st.write("No gaps found: every topic in the notes is explained.")
    with t4:
        if pack["removed"]:
            for q in pack["removed"]:
                st.markdown(f"- ~~{q.get('question', '')}~~  \n  :red[{q.get('removed_because', '')}]")
        else:
            st.write("Nothing was removed.")
    with t5:
        st.json({k: v for k, v in pack.items() if k != "log"}, expanded=False)

    st.download_button("Download study pack (.md)", pipeline.render_markdown(pack),
                       file_name="study_pack.md", mime="text/markdown")
    st.download_button("Download raw JSON", json.dumps(pack, indent=2, ensure_ascii=False),
                       file_name="study_pack.json", mime="application/json")
    st.caption(f"Model: {st.session_state.get('model')} · {pack['api_calls']} API calls")
