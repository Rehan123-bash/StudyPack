# Milestone 2 reel script (about 115 seconds)

Screen recording of the browser with a voice-over. Real runs only. Keep it between 90 and 150 seconds.

## Tabs to open before recording (in this order)

1. App: https://studypack-tokentitans.streamlit.app/
2. v1 prompt: https://github.com/Rehan123-bash/StudyPack/blob/main/prompts/v1/P0_single_prompt.txt
3. v1 output: https://github.com/Rehan123-bash/StudyPack/blob/main/test-data/outputs/v1/T01_os_deadlocks.json
4. Final question prompt: https://github.com/Rehan123-bash/StudyPack/blob/main/prompts/final/P3_question_generator.txt
5. Test table: https://github.com/Rehan123-bash/StudyPack/blob/main/test-data/outputs/test_table.md

## Script

| Time | Screen | Say |
|---|---|---|
| 0:00–0:10 | Tab 1, app home page | "Hi, we're Token Titans. Before exams, most of us just reread long lecture notes. StudyPack turns your notes into a summary, key terms and practice questions, and checks every answer against your notes." |
| 0:10–0:25 | Tab 2 (v1 prompt), then Tab 3, scroll to the practice questions | "This was our first prompt: one instruction, plain text out. The answers look fine, but none of its 35 answers on our test notes shows where it came from, and only 1 of 35 questions went beyond memorising." |
| 0:25–0:45 | Tab 4, scroll to rules 3 and 5 | "Our final version is a four-step chain. The notes get line numbers, every answer must copy the exact line it comes from, our code checks that the quote really exists, and a separate verifier prompt removes anything the notes don't support. Now all 49 questions on our test notes link to a verified quote, and apply-level questions went from 3% to 18%." |
| 0:45–1:35 | Tab 1: pick sample T01_os_deadlocks, click Build study pack, wait for the 4 steps, open Practice questions, open one answer, then open Summary & key terms | "Here it is live. I'll pick our OS notes on deadlocks and build a pack. Step one finds the concepts, step two writes the summary, step three the questions, and step four checks every answer. Here's a question; when I open the answer, it shows the exact line from my notes and that it passed the check. And here's the summary and key terms. If notes only name a topic without explaining it, it's flagged under Gaps." |
| 1:35–1:55 | Tab 5, test table | "We tested 14 inputs, including messy OCR text, Hinglish notes and a prompt-injection attack. 13 passed, and we kept the one failure in our report. Next, for Milestone 3: scanned PDFs, an open-source model comparison and tracking weak topics." |
