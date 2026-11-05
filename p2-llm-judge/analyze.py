"""Comprehensive bias and agreement audit for LLM-as-a-Judge.

Calculates:
1. Agreement (X/30) and Cohen's Kappa against human grades.
2. Position Bias: Verdict flips between normal (A, B) and swapped (B, A) orders.
3. Length Bias: Perturbation test on 10 answers with zero-information padding.
4. Self-Preference Bias: Win-rate inflation of the judge's own model family vs human baseline.

Writes results to results/p2_analysis_summary.json and results/p2_bias_report.md.
"""

import os
import sys
import csv
import json
import argparse
from typing import Any, Dict, List, Tuple
from collections import Counter

# Ensure local imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from judge import judge_pair, load_rubric


def compute_cohens_kappa(human_labels: List[str], judge_labels: List[str]) -> Tuple[float, float]:
    """Compute observed agreement and Cohen's Kappa coefficient between two label sets."""
    assert len(human_labels) == len(judge_labels), "Label arrays must be identical length"
    n = len(human_labels)
    if n == 0:
        return 0.0, 0.0

    classes = sorted(list(set(human_labels).union(set(judge_labels))))
    
    # Observed agreement
    matches = sum(1 for h, j in zip(human_labels, judge_labels) if h == j)
    po = matches / n

    # Expected agreement by chance
    human_counts = Counter(human_labels)
    judge_counts = Counter(judge_labels)

    pe = sum((human_counts[c] / n) * (judge_counts[c] / n) for c in classes)

    if pe >= 1.0:
        kappa = 1.0
    else:
        kappa = (po - pe) / (1.0 - pe)

    return round(po, 4), round(kappa, 4)


def run_analysis(
    answers_path: str,
    human_grades_path: str,
    results_dir: str,
    backend: str = None,
    judge_model: str = None,
):
    os.makedirs(results_dir, exist_ok=True)
    rubric = load_rubric()

    # Load paired answers
    with open(answers_path, "r", encoding="utf-8") as f:
        pairs = [json.loads(line) for line in f if line.strip()]

    # Load human grades
    human_grades = {}
    with open(human_grades_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            human_grades[row["question_id"]] = row["human_winner"].strip().upper()

    print(f"Loaded {len(pairs)} answers and {len(human_grades)} human annotations.")

    # =========================================================================
    # 1. EVALUATION IN BOTH ORDERS (Position Bias & Agreement)
    # =========================================================================
    print("\n[Step 1] Evaluating Normal and Swapped Presentation Orders...")
    normal_verdicts = []
    swapped_verdicts = []
    position_flips = []

    human_list = []
    judge_normal_list = []
    judge_swapped_list = []

    for p in pairs:
        qid = p["id"]
        q = p["question"]
        ans_a = p["answer_a"]
        ans_b = p["answer_b"]
        h_winner = human_grades.get(qid, "TIE")

        # Judge Normal (Candidate 1 = A, Candidate 2 = B)
        norm_res = judge_pair(q, ans_a, ans_b, swap_order=False, rubric_text=rubric, backend=backend, model=judge_model)
        w_norm = norm_res["winner"]
        normal_verdicts.append(norm_res)

        # Judge Swapped (Candidate 1 = B, Candidate 2 = A)
        swap_res = judge_pair(q, ans_a, ans_b, swap_order=True, rubric_text=rubric, backend=backend, model=judge_model)
        w_swap = swap_res["winner"]
        swapped_verdicts.append(swap_res)

        human_list.append(h_winner)
        judge_normal_list.append(w_norm)
        judge_swapped_list.append(w_swap)

        # Check for position flip
        if w_norm != w_swap:
            position_flips.append({
                "question_id": qid,
                "question": q,
                "winner_normal": w_norm,
                "winner_swapped": w_swap,
                "human_winner": h_winner,
                "raw_choice_normal": norm_res["raw_choice"],
                "raw_choice_swapped": swap_res["raw_choice"],
                "reason_normal": norm_res["reason"],
                "reason_swapped": swap_res["reason"],
            })

    # Calculate Agreement & Cohen's Kappa for Normal Order
    acc_normal, kappa_normal = compute_cohens_kappa(human_list, judge_normal_list)
    raw_agree_count_normal = sum(1 for h, j in zip(human_list, judge_normal_list) if h == j)

    # Position bias metrics
    c1_wins_normal = sum(1 for r in normal_verdicts if r["raw_choice"] == "1")
    c1_wins_swapped = sum(1 for r in swapped_verdicts if r["raw_choice"] == "1")
    flip_count = len(position_flips)

    # =========================================================================
    # 2. LENGTH BIAS TEST (10 Perturbed Answers)
    # =========================================================================
    print("\n[Step 2] Running Length Bias Audit on 10 Answers...")
    # Zero-information padding
    ZERO_INFO_PADDING = (
        "\n\nAdditionally, it is worth emphasizing that system architectures in real-world scenarios "
        "naturally reflect continuous evolution across multiple operational dimensions, balancing "
        "general engineering considerations with overall holistic performance metrics."
    )

    length_test_sample = pairs[:10]
    length_bias_flips = 0
    length_details = []

    for p in length_test_sample:
        qid = p["id"]
        q = p["question"]
        ans_a_orig = p["answer_a"]
        ans_b = p["answer_b"]

        # Original verdict
        orig_verdict = judge_pair(q, ans_a_orig, ans_b, swap_order=False, rubric_text=rubric, backend=backend, model=judge_model)["winner"]

        # Perturbed verdict with padded Answer A
        ans_a_padded = ans_a_orig + ZERO_INFO_PADDING
        padded_verdict = judge_pair(q, ans_a_padded, ans_b, swap_order=False, rubric_text=rubric, backend=backend, model=judge_model)["winner"]

        gained_win = (orig_verdict != "A" and padded_verdict == "A")
        if gained_win:
            length_bias_flips += 1

        length_details.append({
            "question_id": qid,
            "orig_len_a": len(ans_a_orig.split()),
            "padded_len_a": len(ans_a_padded.split()),
            "len_b": len(ans_b.split()),
            "original_winner": orig_verdict,
            "padded_winner": padded_verdict,
            "gained_win_via_length": gained_win,
        })

    # =========================================================================
    # 3. SELF-PREFERENCE BIAS AUDIT
    # =========================================================================
    print("\n[Step 3] Computing Self-Preference Bias Audit...")
    # Model A is Concise-Engineer, Model B is Verbose-Academic
    # Compare Judge's preference for A vs Human's preference for A
    judge_a_wins = sum(1 for w in judge_normal_list if w == "A")
    judge_b_wins = sum(1 for w in judge_normal_list if w == "B")
    judge_ties = sum(1 for w in judge_normal_list if w == "TIE")

    human_a_wins = sum(1 for w in human_list if w == "A")
    human_b_wins = sum(1 for w in human_list if w == "B")
    human_ties = sum(1 for w in human_list if w == "TIE")

    # =========================================================================
    # 4. SAVE COMPREHENSIVE RESULTS
    # =========================================================================
    summary = {
        "dataset_size": len(pairs),
        "agreement": {
            "agreed_count": raw_agree_count_normal,
            "total": len(pairs),
            "accuracy_pct": round(acc_normal * 100, 2),
            "cohens_kappa": kappa_normal,
        },
        "position_bias": {
            "position_flips_count": flip_count,
            "flip_rate_pct": round((flip_count / len(pairs)) * 100, 2),
            "cand1_win_rate_normal_pct": round((c1_wins_normal / len(pairs)) * 100, 2),
            "cand1_win_rate_swapped_pct": round((c1_wins_swapped / len(pairs)) * 100, 2),
            "flipped_examples": position_flips[:3],
        },
        "length_bias": {
            "samples_tested": len(length_test_sample),
            "wins_gained_by_padding": length_bias_flips,
            "length_bias_flip_rate_pct": round((length_bias_flips / len(length_test_sample)) * 100, 2),
            "details": length_details,
        },
        "self_preference": {
            "judge_distribution": {"A": judge_a_wins, "B": judge_b_wins, "TIE": judge_ties},
            "human_distribution": {"A": human_a_wins, "B": human_b_wins, "TIE": human_ties},
            "judge_win_rate_a_pct": round((judge_a_wins / len(pairs)) * 100, 2),
            "human_win_rate_a_pct": round((human_a_wins / len(pairs)) * 100, 2),
            "self_preference_delta_pct": round(((judge_a_wins - human_a_wins) / len(pairs)) * 100, 2),
        },
    }

    summary_file = os.path.join(results_dir, "p2_analysis_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nSaved numerical summary to: {summary_file}")

    # Write Markdown Report
    report_file = os.path.join(results_dir, "p2_bias_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# Project 2: LLM-as-a-Judge Audit Report\n\n")
        f.write("## 1. Agreement with Human Ground Truth\n")
        f.write(f"- **Raw Agreement:** {raw_agree_count_normal}/{len(pairs)} ({summary['agreement']['accuracy_pct']}%)\n")
        f.write(f"- **Cohen's Kappa (κ):** {kappa_normal:.4f}\n\n")

        f.write("## 2. Position Bias Audit\n")
        f.write(f"- **Flipped Verdicts on Swap:** {flip_count}/{len(pairs)} ({summary['position_bias']['flip_rate_pct']}%)\n")
        f.write(f"- **Candidate 1 Win Rate (Normal Order):** {summary['position_bias']['cand1_win_rate_normal_pct']}%\n")
        f.write(f"- **Candidate 1 Win Rate (Swapped Order):** {summary['position_bias']['cand1_win_rate_swapped_pct']}%\n\n")

        f.write("## 3. Length Bias Audit (Zero-Information Padding)\n")
        f.write(f"- **Wins Gained purely by Padding:** {length_bias_flips}/{len(length_test_sample)} ({summary['length_bias']['length_bias_flip_rate_pct']}%)\n\n")

        f.write("## 4. Self-Preference & Distribution Comparison\n")
        f.write("| Verdict | Human Count | Judge Count | Difference |\n")
        f.write("| :--- | :---: | :---: | :---: |\n")
        f.write(f"| Model A (Concise) | {human_a_wins} | {judge_a_wins} | {judge_a_wins - human_a_wins:+d} |\n")
        f.write(f"| Model B (Verbose) | {human_b_wins} | {judge_b_wins} | {judge_b_wins - human_b_wins:+d} |\n")
        f.write(f"| Tie | {human_ties} | {judge_ties} | {judge_ties - human_ties:+d} |\n\n")

    print(f"Saved audit report to: {report_file}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Analyze LLM Judge biases and human agreement")
    parser.add_argument("--answers", default=os.path.join(SCRIPT_DIR, "answers.jsonl"))
    parser.add_argument("--human-grades", default=os.path.join(SCRIPT_DIR, "human_grades.csv"))
    parser.add_argument("--results-dir", default=os.path.join(REPO_ROOT, "results"))
    parser.add_argument("--backend", default=None)
    parser.add_argument("--model", default=None)

    args = parser.parse_args()
    run_analysis(
        answers_path=args.answers,
        human_grades_path=args.human_grades,
        results_dir=args.results_dir,
        backend=args.backend,
        judge_model=args.model,
    )


if __name__ == "__main__":
    main()
