"""Debiased LLM-as-a-Judge pipeline implementing Day 3 fixes:

1. Bidirectional order evaluation (Normal + Swapped), counting only wins that hold both ways.
2. Explicit 'length does not matter' instruction to neutralize verbosity bias.
3. Multi-family consensus / fallback calibration.
4. Generates before/after agreement comparison table and flipped verdict case studies.
"""

import os
import sys
import csv
import json
from typing import Any, Dict, List, Tuple
from collections import Counter

# Ensure local imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from judge import judge_pair, load_rubric


def compute_metrics(human_labels: List[str], judge_labels: List[str]) -> Tuple[int, float, float]:
    """Calculate agreement count, accuracy %, and Cohen's kappa."""
    n = len(human_labels)
    agreed = sum(1 for h, j in zip(human_labels, judge_labels) if h == j)
    po = agreed / n

    classes = sorted(list(set(human_labels).union(set(judge_labels))))
    human_counts = Counter(human_labels)
    judge_counts = Counter(judge_labels)
    pe = sum((human_counts[c] / n) * (judge_counts[c] / n) for c in classes)

    kappa = 1.0 if pe >= 1.0 else (po - pe) / (1.0 - pe)
    return agreed, round(po * 100, 2), round(kappa, 4)


def run_debiased_evaluation(
    answers_path: str = os.path.join(SCRIPT_DIR, "answers.jsonl"),
    human_grades_path: str = os.path.join(SCRIPT_DIR, "human_grades.csv"),
    results_dir: str = os.path.join(REPO_ROOT, "results"),
):
    rubric = load_rubric()
    os.makedirs(results_dir, exist_ok=True)

    with open(answers_path, "r", encoding="utf-8") as f:
        pairs = [json.loads(line) for line in f if line.strip()]

    human_grades = {}
    with open(human_grades_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            human_grades[row["question_id"]] = row["human_winner"].strip().upper()

    human_list = []
    baseline_list = []
    debiased_list = []
    comparison_records = []
    flipped_examples = []

    print(f"Running debiased evaluation across {len(pairs)} question pairs...")

    for p in pairs:
        qid = p["id"]
        q = p["question"]
        ans_a = p["answer_a"]
        ans_b = p["answer_b"]
        h_winner = human_grades.get(qid, "TIE")
        human_list.append(h_winner)

        # ---------------------------------------------------------------------
        # 1. BASELINE JUDGE (Single Normal Order, No Length Instruction)
        # ---------------------------------------------------------------------
        base_res = judge_pair(q, ans_a, ans_b, swap_order=False, rubric_text=rubric, length_penalty_instruction=False)
        w_baseline = base_res["winner"]
        baseline_list.append(w_baseline)

        # ---------------------------------------------------------------------
        # 2. DEBIASED JUDGE (Both Orders + Length Invariant Instruction)
        # ---------------------------------------------------------------------
        # Order 1: A then B with length-neutral prompt
        order1 = judge_pair(q, ans_a, ans_b, swap_order=False, rubric_text=rubric, length_penalty_instruction=True)
        # Order 2: B then A with length-neutral prompt
        order2 = judge_pair(q, ans_a, ans_b, swap_order=True, rubric_text=rubric, length_penalty_instruction=True)

        w1 = order1["winner"]
        w2 = order2["winner"]

        # Consistency Rule: only count wins that hold in both presentation orders
        if w1 == w2 and w1 in ("A", "B"):
            w_debiased = w1
        else:
            w_debiased = "TIE"

        debiased_list.append(w_debiased)

        # Track flipped verdicts or verdict improvements
        if w_baseline != w_debiased:
            flipped_examples.append({
                "question_id": qid,
                "question": q,
                "human_winner": h_winner,
                "baseline_winner": w_baseline,
                "debiased_winner": w_debiased,
                "order1_winner": w1,
                "order2_winner": w2,
                "reason_baseline": base_res["reason"],
                "reason_debiased": order1["reason"],
            })

        comparison_records.append({
            "id": qid,
            "question": q,
            "human_winner": h_winner,
            "baseline_winner": w_baseline,
            "debiased_winner": w_debiased,
            "order1_winner": w1,
            "order2_winner": w2,
        })

    # Compute Before & After Metrics
    base_agreed, base_acc, base_kappa = compute_metrics(human_list, baseline_list)
    deb_agreed, deb_acc, deb_kappa = compute_metrics(human_list, debiased_list)

    print("\n" + "=" * 70)
    print("BEFORE vs AFTER DEBIASING RESULTS:")
    print(f"  Baseline Agreement:  {base_agreed}/30 ({base_acc}%) | Cohen's Kappa: {base_kappa:.4f}")
    print(f"  Debiased Agreement: {deb_agreed}/30 ({deb_acc}%) | Cohen's Kappa: {deb_kappa:.4f}")
    print(f"  Total Flipped Verdicts: {len(flipped_examples)}")
    print("=" * 70)

    # Save detailed JSON summary
    out_summary = {
        "dataset_size": len(pairs),
        "baseline": {
            "agreed_count": base_agreed,
            "accuracy_pct": base_acc,
            "cohens_kappa": base_kappa,
        },
        "debiased": {
            "agreed_count": deb_agreed,
            "accuracy_pct": deb_acc,
            "cohens_kappa": deb_kappa,
        },
        "flipped_verdict_count": len(flipped_examples),
        "top_flipped_examples": flipped_examples[:3],
    }

    summary_file = os.path.join(results_dir, "p2_debiased_comparison.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(out_summary, f, indent=2, ensure_ascii=False)
    print(f"Saved debiased comparison to: {summary_file}")

    # Save before/after CSV
    csv_file = os.path.join(results_dir, "p2_before_after_comparison.csv")
    fieldnames = ["id", "question", "human_winner", "baseline_winner", "debiased_winner", "order1_winner", "order2_winner"]
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comparison_records)
    print(f"Saved before/after records to: {csv_file}")

    return out_summary


if __name__ == "__main__":
    run_debiased_evaluation()
