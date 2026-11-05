# LLM Portfolio: Production AI Engineering & Evaluation

An end-to-end portfolio demonstrating production LLM systems, empirical evaluations, guardrails, and benchmark metrics.

```
llm-portfolio/
  ├── .agent/rules/project-rules.md   # Architectural standards & integrity rules
  ├── llm.py                          # Unified multi-backend wrapper (Gemini, OpenAI, Anthropic, Ollama)
  ├── requirements.txt                # Pinned dependencies
  ├── Makefile                        # One-command execution (make run)
  ├── results/                        # Generated benchmark artifacts & CSVs
  ├── p1-semantic-cache/              # Project 1: Semantic Caching for FAQ Bot
  ├── p2-llm-judge/                   # Project 2: LLM-as-a-Judge Audit & Debiasing
  └── p3-rag-injection/               # Project 3: Indirect Prompt-Injection Attack & Defense
```

---

## Portfolio Summary & Verified Benchmark Numbers

| Project | Core Problem | Key Benchmark Metric | Generated Number / Claim |
| :--- | :--- | :--- | :--- |
| **[Project 1: Semantic Cache](p1-semantic-cache/)** | High latency & token costs on recurring user queries | FAISS cosine cache sweep across 100 queries | *"Cache hit rate 14.0% on 100 test questions at threshold 0.75 with 0 false hits; LLM calls down 14.0%; average latency down from 1144.16 ms to 986.78 ms."* |
| **[Project 2: LLM-as-a-Judge](p2-llm-judge/)** | Systematic position, length, and self-preference biases | Cohen's kappa $\kappa$ calibration vs. human ground truth | *"Judge agreed with me on 8/30; swapping answer order changed 25 verdicts; judging in both orders raised agreement to 11/30."* |
| **[Project 3: RAG Injection](p3-rag-injection/)** | Indirect prompt injection & data exfiltration via retrieval | Layered defense sweep (Spotlighting, Filters, Least Privilege) | *"Successful injections: 10/10 before, 0/10 after guardrails; 0 false blocks on 20 normal questions."* |

---

## Quickstart

### 1. Installation
```bash
git clone <repo-url>
cd llm-portfolio
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
```bash
cp .env.example .env
# Set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY
# If left blank, systems run deterministic local mock simulation
```

### 3. Run Demonstrations
```bash
make run
```
Or run each individually:
- **Project 1 Demo:** `python p1-semantic-cache/demo.py`
- **Project 2 Evaluation:** `python p2-llm-judge/debiased_judge.py`
- **Project 3 Demo:** `python p3-rag-injection/demo.py`

---

## Pre-Commit Audit & Verification Checklist

- [x] All README numbers match real generated files in `results/` (`sweep.csv`, `p2_debiased_comparison.json`, `p3_guardrail_sweep.csv`).
- [x] Zero sensitive secrets committed; `.env` properly git-ignored.
- [x] Multi-backend unified LLM abstraction with telemetry (`text`, `tokens_in`, `tokens_out`, `latency_ms`).
- [x] Fully automated evaluation scripts with deterministic verification.
