# Project Rules for LLM Portfolio

These rules govern code structure, evaluation integrity, and safety across all projects in this portfolio (`p1-semantic-cache`, `p2-llm-judge`, `p3-rag-injection`).

## 1. Secrets & Credentials
- NEVER commit `.env`, API keys, passwords, or personal credentials.
- All code must load environment variables through `python-dotenv` with sensible fallbacks and clear error messages when keys are absent.

## 2. Shared LLM Abstraction
- All LLM calls must go through `llm.py:chat(messages, temperature=0, max_tokens=500)`.
- The returned dict must strictly contain:
  - `text`: str
  - `tokens_in`: int
  - `tokens_out`: int
  - `latency_ms`: float
- Backends must support: `openai`, `anthropic`, `gemini`, and `ollama`, controlled by `LLM_BACKEND` and `LLM_MODEL`.

## 3. Evaluation Integrity
- README metrics (hit rates, latency numbers, Cohen's kappa, attack success rates, false blocks) must come directly from real execution results stored in `results/`.
- Never hardcode or fabricate benchmark figures.
- Provide clean CLI scripts and reproducible sweeps for all test scenarios.

## 4. Code Standards & Modularity
- Each project must be self-contained in its designated subfolder (`p1-semantic-cache/`, `p2-llm-judge/`, `p3-rag-injection/`).
- Use typed Python with docstrings and modular components (e.g. `cache.py`, `bot.py`, `logger.py`, `judge.py`).
- Maintain clean logging (JSONL/CSV) for all evaluation runs.
