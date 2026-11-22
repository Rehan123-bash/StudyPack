# Changelog

## 2026-11-22
- First test run in GitHub Actions failed on every call: the Gemini v1 endpoint rejected system instructions (400 INVALID_ARGUMENT). Fixed by using the v1beta API; the test runner now retries saved runs that ended in an error.
- Added screenshot script (code/screenshots.py) that runs real test inputs through the app and saves screenshots for the report.
- Added final 4-step prompt chain P1–P4 (`prompts/final/`): concept extractor with input check, summary and key terms, question generator, verifier.
- Added line-numbered notes and exact source quotes for every answer, checked by code (feedback from Milestone 1: "show where each answer comes from").
- Added gap flags for topics the notes mention but never explain (feedback: "flag gaps, not just errors").
- Added Bloom's-level difficulty mix and question formats: mixed, MCQ, short answer, flashcards (feedback: "mix difficulty", "let students choose the format").
- Added prompt-injection rule: text inside notes is data, not instructions.
- Kept older prompt versions for comparison: v1 (single prompt from Milestone 1), v2 (3-step JSON chain).
- Added Streamlit app (`code/app.py`) with paste, .txt/.md/text-PDF upload, sample notes, downloads.
- Added test set of 14 cases (7 normal, 5 edge, 2 invalid) and test runner with E1 judge prompt for version comparison.
- Added diagrams: prompt workflow, task decomposition, input–output flow, system architecture.
- Changed from Milestone 1: grounding is done by putting the whole notes in the prompt (context injection) rather than vector retrieval, because one topic's notes fit easily in the model's context. Llama (Groq) comparison moved to Milestone 3.

## 2026-10-09
- Milestone 1 submitted: problem C2, baseline prompt v1, feedback from Samriddhi Bhattacharya.
