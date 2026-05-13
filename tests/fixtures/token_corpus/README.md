# Token Corpus

Public-domain prose excerpts plus synthetic edge cases for
`test_tokens_accuracy.py`. Total budget: under 500KB.

Files:

- `austen.txt` — Pride and Prejudice opening, ~700 words. Plain prose.
- `dickens.txt` — A Tale of Two Cities opening, ~400 words. Plain prose.
- `dialogue.txt` — Synthetic dialogue-heavy excerpt with em-dashes,
  contractions, and short turns.
- `nonlatin.txt` — Synthetic multi-script excerpt (Cyrillic, CJK, Arabic)
  exercising the "characters per token" assumption.
- `expected.json` — Per-file expected token count from the reference
  tokenizer (here: heuristic; in S6 we update against tiktoken).
