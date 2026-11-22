# Prompt version comparison (normal test cases 1-7, model gemini-3.5-flash-lite)

| Version | Test cases | Runs OK | Valid JSON | Questions shown to student | Supported by notes (judge) | Apply/Analyze or higher (judge) | Outside facts in summary/terms (judge) | Questions with verified source link | Avg seconds per pack | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| v1 | 7 | 7 | n/a (plain text) | 35 | 35/35 (100%) | 1/35 (3%) | 0 | 0/35 | 4.2 |  |
| v2 | 7 | 7 | 21/21 steps | 49 | 49/49 (100%) | 0/49 (0%) | 0 | 0/49 | 8.1 |  |
| v3 | 7 | 7 | 26/28 steps | 49 | 49/49 (100%) | 9/49 (18%) | 0 | 49/49 | 13.3 | 0 of 49 generated questions removed by checker |
