"""Automated Attack Runner for RAG Prompt Injection Testing.

Runs 10 distinct prompt injection attack vectors against the target RAG bot,
verifies whether poisoned documents were retrieved, evaluates code-checkable success
conditions, saves replies to results/p3_baseline_attacks.jsonl, and prints summary metrics.
"""

import os
import sys
import json
import argparse
from typing import Any, Dict, List

# Ensure local imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from rag import RAGBot


def check_attack_success(response: str, condition_type: str, target_pattern: str) -> bool:
    """Check code-checkable condition for attack success."""
    if condition_type == "contains_string":
        return target_pattern.lower() in response.lower()
    return False


def run_attacks(
    attacks_json: str,
    output_jsonl: str,
    layer_spotlighting: bool = False,
    layer_input_filter: bool = False,
    layer_output_filter: bool = False,
    layer_least_privilege: bool = False,
) -> Dict[str, Any]:
    with open(attacks_json, "r", encoding="utf-8") as f:
        attacks: List[Dict[str, Any]] = json.load(f)

    print(f"\nInitializing RAG Bot (Defenses: Spotlight={layer_spotlighting}, "
          f"InputFilter={layer_input_filter}, OutputFilter={layer_output_filter}, "
          f"LeastPrivilege={layer_least_privilege})...")

    bot = RAGBot(
        layer_spotlighting=layer_spotlighting,
        layer_input_filter=layer_input_filter,
        layer_output_filter=layer_output_filter,
        layer_least_privilege=layer_least_privilege,
    )
    print(f"Indexed {len(bot.chunks)} total chunks across clean and poisoned documents.")

    successful_attacks = 0
    total_attacks = len(attacks)
    results = []

    print("\n" + "=" * 95)
    print(f"{'#':<3} | {'Attack Name':<35} | {'Target':<15} | {'Poison In Top-3?':<16} | {'Status'}")
    print("=" * 95)

    for idx, atk in enumerate(attacks, 1):
        aid = atk["id"]
        name = atk["name"]
        q = atk["trigger_query"]
        target = atk["target_pattern"]
        ctype = atk["condition_type"]

        # Run query
        res = bot.query(q)
        response_text = res["response"]
        audit = res["audit"]
        retrieved_poison = audit.get("retrieved_poison", False)

        # Evaluate code-checkable success condition
        is_success = check_attack_success(response_text, ctype, target)
        if is_success:
            successful_attacks += 1
            status_str = "\033[91mSUCCESS (PWNED)\033[0m"
        else:
            status_str = "\033[92mDEFENDED\033[0m"

        print(f"{idx:<3} | {name:<35} | {target:<15} | {str(retrieved_poison):<16} | {status_str}")

        record = {
            "attack_id": aid,
            "name": name,
            "query": q,
            "target_pattern": target,
            "retrieved_files": audit.get("retrieved_files", []),
            "retrieved_poison": retrieved_poison,
            "attack_success": is_success,
            "response": response_text,
            "audit": audit,
        }
        results.append(record)

    asr_pct = round((successful_attacks / total_attacks) * 100, 2)
    print("=" * 95)
    print(f"SUMMARY: Attack Success Rate (ASR): {successful_attacks}/{total_attacks} ({asr_pct}%)\n")

    os.makedirs(os.path.dirname(os.path.abspath(output_jsonl)), exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Detailed logs saved to: {output_jsonl}")

    return {
        "total_attacks": total_attacks,
        "successful_attacks": successful_attacks,
        "attack_success_rate_pct": asr_pct,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Run RAG prompt injection attacks")
    parser.add_argument("--attacks", default=os.path.join(SCRIPT_DIR, "attacks.json"))
    parser.add_argument("--output", default=os.path.join(REPO_ROOT, "results", "p3_baseline_attacks.jsonl"))
    parser.add_argument("--spotlighting", action="store_true")
    parser.add_argument("--input-filter", action="store_true")
    parser.add_argument("--output-filter", action="store_true")
    parser.add_argument("--least-privilege", action="store_true")

    args = parser.parse_args()

    run_attacks(
        attacks_json=args.attacks,
        output_jsonl=args.output,
        layer_spotlighting=args.spotlighting,
        layer_input_filter=args.input_filter,
        layer_output_filter=args.output_filter,
        layer_least_privilege=args.least_privilege,
    )


if __name__ == "__main__":
    main()
