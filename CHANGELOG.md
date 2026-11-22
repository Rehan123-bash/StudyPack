# Changelog

## 2026-11-22
- Fourth test run (gemini-3.5-flash-lite, chosen automatically): 12 of 14 tests passed. Test 5 crashed because a prompt returned a JSON list instead of an object; the app crashed the same way once in the screenshot run (test 1). Fixed: the parser now repairs list replies and skips non-object items, and records the step as not strictly valid JSON. The app now shows the error message instead of hiding it. Test 12 failed honestly (9 questions from 4-line notes); kept as a known limitation.
- Third test run failed: gemini-2.5-flash-lite is no longer available to new API users (404 NOT_FOUND). Added code/probe_models.py, which picks the first model that works on our free tier before each run; the test runner now stops at the first refused request.
- Second test run stopped at the first call: the free-tier daily limit for gemini-2.5-flash on our project was already used up (the failed first run also counted). Switched the app and tests to gemini-2.5-flash-lite, which has its own daily limit, and added an optional backup key (GEMINI_API_KEY_2) for long test runs. Deleted the outputs of the two failed runs (still in git history) so all results come from one model.
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
