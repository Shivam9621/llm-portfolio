.PHONY: run run-p1 run-p2 run-p3 test install

install:
	pip install -r requirements.txt

run: run-p1 run-p2 run-p3
	@echo "=================================================="
	@echo "All portfolio project demonstrations ran cleanly!"
	@echo "=================================================="

run-p1:
	@echo "\n>>> Running Project 1 (Semantic Cache Demo) <<<"
	python p1-semantic-cache/demo.py

run-p2:
	@echo "\n>>> Running Project 2 (LLM Judge Debiased Evaluation) <<<"
	python p2-llm-judge/debiased_judge.py

run-p3:
	@echo "\n>>> Running Project 3 (RAG Injection Defense Demo) <<<"
	python p3-rag-injection/demo.py

test:
	python p1-semantic-cache/sweep.py
	python p2-llm-judge/analyze.py
	python p3-rag-injection/guardrails_eval.py
