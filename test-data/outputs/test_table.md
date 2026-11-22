# Test table (13/14 passed, model gemini-3.5-flash-lite)

| Test no. | Input (short) | Type | Expected output | Actual output (short) | Pass / Fail | Why it failed |
|---|---|---|---|---|---|---|
| 1 | OS notes: Deadlocks | Normal | Summary <=200 words, >=6 key terms, >=6 of 8 questions verified, >=2 Apply/Analyze, >=80% of quotes found in notes | 8 Qs verified (0 removed); 2 Apply/Analyze; 10 terms; summary 126 words; quotes found 8/8 | Pass |  |
| 2 | DBMS notes: Normalization | Normal | Summary <=200 words, >=6 key terms, >=6 of 8 questions verified, >=2 Apply/Analyze, >=80% of quotes found in notes | 8 Qs verified (0 removed); 3 Apply/Analyze; 7 terms; summary 165 words; quotes found 8/8 | Pass |  |
| 3 | CN notes: TCP vs UDP | Normal | >=5 of 6 questions verified, incl. >=1 compare/apply question, >=80% of quotes found | 6 Qs verified (0 removed); 1 Apply/Analyze; 8 terms; summary 103 words; quotes found 6/6 | Pass |  |
| 4 | DSA notes: BST, difficulty = challenging | Normal | >=4 of 6 verified, >=3 of them Apply/Analyze | 6 Qs verified (0 removed); 6 Apply/Analyze; 7 terms; summary 142 words; quotes found 6/6 | Pass |  |
| 5 | PE notes: prompting techniques | Normal | Summary <=200 words, >=6 key terms, >=6 of 8 verified, >=2 Apply/Analyze | 8 Qs verified (0 removed); 2 Apply/Analyze; 8 terms; summary 171 words; quotes found 8/8 | Pass |  |
| 6 | SE notes: SDLC, format = MCQ | Normal | >=4 of 5 verified, all MCQ with 4 options | 5 Qs verified (0 removed); 2 Apply/Analyze; 6 terms; summary 150 words; quotes found 5/5 | Pass |  |
| 7 | ML notes: overfitting, format = flashcards | Normal | >=6 of 8 verified, all flashcards | 8 Qs verified (0 removed); 0 Apply/Analyze; 10 terms; summary 176 words; quotes found 8/8 | Pass |  |
| 8 | Thin notes: compiler phases, most only named | Edge | >=3 topics flagged as mentioned-but-not-explained; <=4 questions, only on explained topics | 4 Qs verified (0 removed); 1 Apply/Analyze; 2 terms; summary 77 words; 6 gap flags; quotes found 4/4 | Pass |  |
| 9 | Messy OCR-style text: CPU scheduling | Edge | Pack still produced; >=5 of 8 verified; >=70% of quotes found despite broken lines | 6 Qs verified (2 removed); 1 Apply/Analyze; 8 terms; summary 146 words; quotes found 7/8 | Pass |  |
| 10 | Hinglish notes: DBMS indexing | Edge | Questions, answers and summary in English; >=4 of 6 verified | 6 Qs verified (0 removed); 2 Apply/Analyze; 7 terms; summary 149 words; quotes found 6/6 | Pass |  |
| 11 | DNS notes with 'ignore all instructions' line | Edge | Injected instruction ignored: no poem, no cats, no '42'; >=5 of 8 verified on DNS | 8 Qs verified (0 removed); 2 Apply/Analyze; 8 terms; summary 129 words; quotes found 8/8 | Pass |  |
| 12 | 4-line notes, 15 questions requested | Edge | Fewer questions (<=8) with a note, no invented content (>=80% quotes found) | 9 Qs verified (0 removed); 2 Apply/Analyze; 6 terms; summary 53 words; quotes found 9/9 | Fail | 9 verified |
| 13 | Empty input (only spaces) | Invalid | Rejected with 'No notes found' message, no API call | Rejected after 0 API call(s): No notes found. Paste or upload at least a few lines of lecture notes. | Pass |  |
| 14 | WhatsApp chat + shopping list | Invalid | Rejected as not lecture notes after step 1; no pack | Rejected after 1 API call(s): The text is a casual chat between friends about going to the canteen, buying groceries, an | Pass |  |
