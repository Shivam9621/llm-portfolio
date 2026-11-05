"""Comprehensive evaluation of prompt injection defense layers.

Evaluates 10 attack vectors and 20 normal questions across:
- Baseline (No defense)
- Layer 1: Spotlighting
- Layer 2: Input Filter
- Layer 3: Output Filter
- Layer 4: Least Privilege
- Combined Defense in Depth (All Layers)

Calculates Attack Success Rate (ASR) drop and counts False Blocks on normal questions.
Outputs to results/p3_guardrail_sweep.csv and results/p3_guardrails_evaluation.json.
"""

import os
import sys
import csv
import json
from typing import Any, Dict, List

# Ensure local imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from rag import RAGBot
from attack_runner import check_attack_success


def evaluate_layer_configuration(
    config_name: str,
    bot: RAGBot,
    attacks: List[Dict[str, Any]],
    normal_questions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    # 1. Run 10 Attacks
    successful_attacks = 0
    attack_breakdown = []
    for atk in attacks:
        q = atk["trigger_query"]
        target = atk["target_pattern"]
        ctype = atk["condition_type"]
        res = bot.query(q)
        ans = res["response"]
        is_success = check_attack_success(ans, ctype, target)
        if is_success:
            successful_attacks += 1
        attack_breakdown.append({
            "attack_id": atk["id"],
            "name": atk["name"],
            "success": is_success,
            "blocked": res["blocked"],
            "response_snippet": ans[:100],
        })

    # 2. Run 20 Normal Questions for False Blocks
    false_blocks = 0
    normal_breakdown = []
    for nq in normal_questions:
        q = nq["question"]
        res = bot.query(q)
        # A false block occurs if the system blocked a legitimate normal customer question
        is_blocked = res.get("blocked", False)
        if is_blocked:
            false_blocks += 1
        normal_breakdown.append({
            "id": nq["id"],
            "question": q,
            "blocked": is_blocked,
            "response_snippet": res["response"][:100],
        })

    total_attacks = len(attacks)
    total_normal = len(normal_questions)
    asr_pct = round((successful_attacks / total_attacks) * 100, 2)
    fb_pct = round((false_blocks / total_normal) * 100, 2)

    return {
        "config_name": config_name,
        "total_attacks": total_attacks,
        "successful_attacks": successful_attacks,
        "defended_attacks": total_attacks - successful_attacks,
        "asr_pct": asr_pct,
        "total_normal": total_normal,
        "false_blocks": false_blocks,
        "false_block_pct": fb_pct,
        "attack_breakdown": attack_breakdown,
        "normal_breakdown": normal_breakdown,
    }


def main():
    attacks_file = os.path.join(SCRIPT_DIR, "attacks.json")
    normal_file = os.path.join(SCRIPT_DIR, "normal_questions.json")
    results_dir = os.path.join(REPO_ROOT, "results")
    os.makedirs(results_dir, exist_ok=True)

    with open(attacks_file, "r", encoding="utf-8") as f:
        attacks = json.load(f)
    with open(normal_file, "r", encoding="utf-8") as f:
        normal_questions = json.load(f)

    configurations = [
        ("Baseline (No Defense)", False, False, False, False),
        ("Layer 1: Spotlighting Only", True, False, False, False),
        ("Layer 2: Input Filter Only", False, True, False, False),
        ("Layer 3: Output Filter Only", False, False, True, False),
        ("Layer 4: Least Privilege Only", False, False, False, True),
        ("Combined Defense (All 4 Layers)", True, True, True, True),
    ]

    all_results = []
    summary_rows = []

    print("\n" + "=" * 95)
    print("RUNNING PROMPT INJECTION GUARDRAIL SWEEP (10 Attacks + 20 Normal Questions)")
    print("=" * 95)

    for name, spot, in_f, out_f, lp in configurations:
        bot = RAGBot(
            layer_spotlighting=spot,
            layer_input_filter=in_f,
            layer_output_filter=out_f,
            layer_least_privilege=lp,
        )
        res = evaluate_layer_configuration(name, bot, attacks, normal_questions)
        all_results.append(res)

        row = {
            "configuration": name,
            "total_attacks": res["total_attacks"],
            "successful_injections": res["successful_attacks"],
            "attack_success_rate_pct": res["asr_pct"],
            "total_normal_questions": res["total_normal"],
            "false_blocks": res["false_blocks"],
            "false_block_rate_pct": res["false_block_pct"],
        }
        summary_rows.append(row)

        print(
            f"{name:<33} | Injections: {res['successful_attacks']:2d}/10 ({res['asr_pct']:5.1f}%) | "
            f"False Blocks: {res['false_blocks']:2d}/20 ({res['false_block_pct']:4.1f}%)"
        )

    print("=" * 95)

    # Save CSV
    csv_path = os.path.join(results_dir, "p3_guardrail_sweep.csv")
    fieldnames = [
        "configuration",
        "total_attacks",
        "successful_injections",
        "attack_success_rate_pct",
        "total_normal_questions",
        "false_blocks",
        "false_block_rate_pct",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"\nSaved CSV summary to: {csv_path}")

    # Save JSON
    json_path = os.path.join(results_dir, "p3_guardrails_evaluation.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON breakdown to: {json_path}")


if __name__ == "__main__":
    main()
