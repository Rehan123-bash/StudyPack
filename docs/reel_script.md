# Milestone 2 reel script (target 110–120 seconds)

Record the screen (OBS, Xbox Game Bar `Win+Alt+R`, or macOS `Cmd+Shift+5`) and record the voice-over at the same time.
Use **real runs only**. Upload to Google Drive or unlisted YouTube, set "Anyone with the link can view", and note the exact length in seconds.

| Time | Screen | Voice-over (read naturally) |
|---|---|---|
| 0:00–0:10 | App home page (title visible) | "Before exams most of us just reread long lecture notes. StudyPack turns your notes into a summary, key terms and practice questions, and checks every answer against your notes." |
| 0:10–0:25 | Open `prompts/v1/P0_single_prompt.txt`, then `test-data/outputs/v1/T01_os_deadlocks.json` (the raw text) | "This was our first prompt from Milestone 1: one instruction, plain text out. It works, but the answers have no source, and we found [say a real number from iteration_metrics, e.g. X of Y answers not supported by the notes]." |
| 0:25–0:45 | Open `prompts/final/P3_question_generator.txt` (scroll to rules 3 and 5), then P4 | "Our final version is a four-step chain. Notes are line-numbered, every answer must quote the exact line it comes from, code checks the quote really exists, and a verifier prompt removes anything the notes don't support. [Say real result, e.g. supported answers went from X% to Y%]." |
| 0:45–1:35 | App: choose a sample (or paste real notes), set format and difficulty, click **Build study pack**; show the 4 steps running; open Practice questions, expand an answer to show the source quote; open Gaps; open Removed by checker | "Here it is running live. I paste OS notes on deadlocks, pick mixed difficulty... step 1 finds the concepts, step 2 writes the summary, step 3 the questions, step 4 checks them. Every answer shows the line it came from. Here are topics the notes only mention, and here's a question the checker removed and why." |
| 1:35–1:55 | Test table (`test-data/outputs/test_table.md`) and the module status table | "We tested 14 inputs, including messy OCR text, Hinglish notes and a prompt-injection attack: [X] passed, and we kept the failures. Next, for Milestone 3: scanned PDFs, a Llama comparison and tracking weak topics." |

Tips: zoom the browser to 125% so text is readable on a phone; keep it between 90 and 150 seconds.
