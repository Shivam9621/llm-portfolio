"""Generates candidate answers for 30 technical questions from two distinct model configurations.

Saves answers to answers.jsonl and produces human_grades_template.csv for blind grading.
"""

import os
import sys
import json
import csv
import argparse

# Ensure repo root is in path for llm.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import llm

# System prompts representing two realistic model behaviors:
# Model A: Concise, direct, bullet-focused senior engineer.
MODEL_A_SYSTEM = (
    "You are a principal backend engineer. Provide a direct, technically rigorous, "
    "and concise answer. Focus on core mechanics, trade-offs, and failure modes. "
    "Do not include conversational filler, intros, or summaries."
)

# Model B: More conversational, explanatory, comprehensive textbook style.
MODEL_B_SYSTEM = (
    "You are a computer science professor. Explain the concept thoroughly, providing "
    "historical context, clear conceptual analogies, and detailed step-by-step explanations "
    "with introductory remarks and concluding takeaways."
)


def generate_answers(
    questions_file: str,
    output_jsonl: str,
    output_csv: str,
    model_a_name: str = "Concise-Engineer",
    model_b_name: str = "Verbose-Academic",
    backend: str = "gemini",
):
    with open(questions_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Loaded {len(questions)} questions from {questions_file}")
    print(f"Generating answers: Model A='{model_a_name}' vs Model B='{model_b_name}'")

    results = []
    csv_rows = []

    for idx, item in enumerate(questions, 1):
        qid = item["id"]
        q_text = item["question"]
        print(f"[{idx}/{len(questions)}] Generating answers for {qid}...")

        # 1. Query Model A
        messages_a = [
            {"role": "system", "content": MODEL_A_SYSTEM},
            {"role": "user", "content": q_text},
        ]
        resp_a = llm.chat(messages_a, temperature=0.2, max_tokens=400, backend=backend)
        ans_a = resp_a.get("text", "").strip()

        # 2. Query Model B
        messages_b = [
            {"role": "system", "content": MODEL_B_SYSTEM},
            {"role": "user", "content": q_text},
        ]
        resp_b = llm.chat(messages_b, temperature=0.4, max_tokens=600, backend=backend)
        ans_b = resp_b.get("text", "").strip()

        record = {
            "id": qid,
            "question": q_text,
            "model_a": model_a_name,
            "answer_a": ans_a,
            "model_b": model_b_name,
            "answer_b": ans_b,
        }
        results.append(record)

        csv_rows.append({
            "question_id": qid,
            "question": q_text,
            "answer_a": ans_a,
            "answer_b": ans_b,
            "human_winner": "",  # To be filled by user: 'A', 'B', or 'tie'
            "human_notes": "",
        })

    # Save answers.jsonl
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nSaved {len(results)} paired answers to: {output_jsonl}")

    # Save human_grades_template.csv
    fieldnames = ["question_id", "question", "answer_a", "answer_b", "human_winner", "human_notes"]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"Saved human grading template to: {output_csv}")


def main():
    parser = argparse.ArgumentParser(description="Generate candidate answers for LLM judge audit")
    parser.add_argument(
        "--questions",
        default=os.path.join(SCRIPT_DIR, "questions.json"),
        help="Path to questions.json",
    )
    parser.add_argument(
        "--output-jsonl",
        default=os.path.join(SCRIPT_DIR, "answers.jsonl"),
        help="Path to save answers.jsonl",
    )
    parser.add_argument(
        "--output-csv",
        default=os.path.join(SCRIPT_DIR, "human_grades_template.csv"),
        help="Path to save human_grades_template.csv",
    )
    parser.add_argument("--model-a", default="Concise-Engineer", help="Label for Model A")
    parser.add_argument("--model-b", default="Verbose-Academic", help="Label for Model B")
    parser.add_argument("--backend", default=None, help="LLM backend override (gemini, openai, etc.)")

    args = parser.parse_args()
    generate_answers(
        questions_file=args.questions,
        output_jsonl=args.output_jsonl,
        output_csv=args.output_csv,
        model_a_name=args.model_a,
        model_b_name=args.model_b,
        backend=args.backend,
    )


if __name__ == "__main__":
    main()
