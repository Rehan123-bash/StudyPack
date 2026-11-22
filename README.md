# StudyPack: Lecture Notes to Verified Study Packs

Prompt Engineering mini-project (SCSE4041), batch 72, faculty: Sonal Kukreja. Problem **C2: Lecture notes to study pack**.

StudyPack turns one topic's lecture notes into a short summary, key terms and practice questions with answers.
Every answer is checked against the notes before the student sees it, and each question shows the exact line of the notes it came from.
Topics the notes only name but never explain are flagged as gaps.

- **Prototype:** `<paste Streamlit app link>`
- **Team:** Token Titans (PE-B65-07)
- **Repository:** https://github.com/rehan123-bash/StudyPack

| Member | Enrollment no. | Main task |
|---|---|---|
| Rehan Ahmad (leader) | S24CSEU2732 | Prompt design (v1 to v3, P1-P4), Streamlit app, deployment, repository, reel |
| Aniket Yadav | S24CSEU2725 | Test set and expected results, test runner and judge prompt E1, test table and error analysis, diagrams, research abstract |

## How it works

A 4-step prompt chain on **Gemini 2.5 Flash-Lite** (Google AI Studio free tier), with code checks between steps:

| Step | Prompt | What it does |
|---|---|---|
| 0 | code | Rejects empty or too-long input; numbers every line of the notes (L1, L2, ...) |
| 1 | `prompts/final/P1_concept_extractor.txt` | Checks the text is lecture notes; lists concepts with line numbers and whether each is *explained* or *mentioned only* |
| 2 | `prompts/final/P2_summary_terms.txt` | Summary (max 200 words) and key terms, each linked to lines |
| 3 | `prompts/final/P3_question_generator.txt` | Questions in the chosen format (mixed / MCQ / short / flashcard) at a Bloom's-level mix, each with answer, source lines and an exact quote |
| code | quote check | Confirms each quote really appears in the notes |
| 4 | `prompts/final/P4_verifier.txt` | Marks each answer SUPPORTED / PARTLY / UNSUPPORTED using only the notes |
| code | filter + gaps | Shows only SUPPORTED answers whose quote was found; lists removed questions and gap flags |

Diagrams are in `docs/diagrams/`.

## Run it

```bash
pip install -r requirements.txt
# put your key in the environment (never in the code)
export GEMINI_API_KEY="your-key"          # Windows PowerShell:  $env:GEMINI_API_KEY="your-key"
streamlit run code/app.py                 # the web app
python code/run_tests.py                  # the 14-case test set + prompt-version comparison
```

Get a free key at https://aistudio.google.com (Get API key). If you hit the free-tier daily limit, run again later
or set `GEMINI_API_KEY_2` to a teammate's key (the daily limit is per Google Cloud project). Saved outputs are reused, so the test runner continues where it stopped.

No Python on your computer? Open `code/run_tests_colab.ipynb` in Google Colab.

## Folders

```
prompts/v1/      baseline single prompt from Milestone 1
prompts/v2/      3-step chain with JSON output
prompts/v3/      4-step chain with line numbers, quotes, verifier, gap flags (= final)
prompts/final/   final prompts P1-P4 used by the app
prompts/eval/    E1 judge prompt, used only for testing
code/            app.py (Streamlit), pipeline.py (chain), llm.py (Gemini client), run_tests.py (tests)
test-data/       inputs/ (14 test notes), test_cases.json (expected results), outputs/ (real runs)
docs/            diagrams, reel script, Milestone 2 PDF
```

## Responsible use

- Gives study help only from the student's own notes; it does not add outside facts on purpose, and answers the checker cannot support are removed.
- AI output can still be wrong. The app says so, and shows the source line so students can check.
- Do not paste personal data. On the Gemini free tier, Google may use inputs to improve its models.
- Text inside the notes is treated as data, not instructions (tested with a prompt-injection case).
- The test notes in `test-data/inputs/` were drafted with AI assistance and reviewed by the team.
