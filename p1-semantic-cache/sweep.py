"""Threshold sweep and benchmark evaluation for Semantic Cache.

Runs thresholds from 0.75 to 0.95 in 0.05 steps across test_set.jsonl.
Evaluates:
- Hit Rate (%)
- False Hits (unrelated queries or mismatched FAQ IDs that exceeded threshold)
- Negation Guard activations (queries blocked due to polarity conflict)
- Average Lookup Latency (ms)

Writes results to results/sweep.csv and logs detailed negation events.
"""

import os
import sys
import csv
import json
import time
from typing import Any, Dict, List

# Ensure local imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from cache import SemanticCache, contains_pii_or_order_id


def run_sweep():
    faqs_path = os.path.join(SCRIPT_DIR, "faqs.json")
    test_set_path = os.path.join(SCRIPT_DIR, "test_set.jsonl")
    results_dir = os.path.join(REPO_ROOT, "results")
    os.makedirs(results_dir, exist_ok=True)
    sweep_csv_path = os.path.join(results_dir, "sweep.csv")
    negation_events_path = os.path.join(results_dir, "negation_events.jsonl")

    # Load test set
    with open(test_set_path, "r", encoding="utf-8") as f:
        test_queries = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(test_queries)} test queries from {test_set_path}")

    # Thresholds: 0.75 to 0.95 in 0.05 steps
    thresholds = [0.75, 0.80, 0.85, 0.90, 0.95]
    summary_rows = []
    all_negation_events = []

    print("\n" + "=" * 80)
    print("RUNNING THRESHOLD SWEEP (0.75 to 0.95)")
    print("=" * 80)

    for thresh in thresholds:
        # Initialize fresh cache for each threshold
        cache = SemanticCache(threshold=thresh, enable_negation_guard=True)
        with open(faqs_path, "r", encoding="utf-8") as f:
            faqs = json.load(f)
        for faq in faqs:
            cache.add(faq["question"], faq["answer"], faq["id"])

        hits = 0
        true_hits = 0
        false_hits = 0
        negation_blocks = 0
        latencies_ms = []

        for item in test_queries:
            q = item["question"]
            expected_id = item["expected_faq_id"]

            t0 = time.perf_counter()
            is_hit, sim, match, audit = cache.lookup(q, threshold=thresh)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(elapsed_ms)

            if audit.get("negation_blocked"):
                negation_blocks += 1
                all_negation_events.append({
                    "threshold": thresh,
                    "query": q,
                    "matched_faq": match["faq_id"] if match else None,
                    "matched_question": audit["matched_question"],
                    "similarity": round(sim, 4),
                })

            if is_hit and match:
                hits += 1
                matched_id = match["faq_id"]
                if expected_id != "none" and matched_id == expected_id:
                    true_hits += 1
                else:
                    false_hits += 1

        total = len(test_queries)
        hit_rate = round((hits / total) * 100, 2)
        false_hit_rate = round((false_hits / total) * 100, 2)
        avg_latency = round(sum(latencies_ms) / len(latencies_ms), 2)

        row = {
            "threshold": f"{thresh:.2f}",
            "total_queries": total,
            "hits": hits,
            "hit_rate_pct": hit_rate,
            "true_hits": true_hits,
            "false_hits": false_hits,
            "false_hit_rate_pct": false_hit_rate,
            "negation_blocks": negation_blocks,
            "avg_latency_ms": avg_latency,
        }
        summary_rows.append(row)

        print(
            f"Threshold: {thresh:.2f} | Hits: {hits:2d}/{total} ({hit_rate:5.1f}%) | "
            f"True Hits: {true_hits:2d} | False Hits: {false_hits:2d} | "
            f"Negation Blocks: {negation_blocks:2d} | Avg Latency: {avg_latency:5.2f} ms"
        )

    # Write summary to CSV
    fieldnames = [
        "threshold",
        "total_queries",
        "hits",
        "hit_rate_pct",
        "true_hits",
        "false_hits",
        "false_hit_rate_pct",
        "negation_blocks",
        "avg_latency_ms",
    ]
    with open(sweep_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"\nSaved sweep results to: {sweep_csv_path}")

    # Write negation events
    with open(negation_events_path, "w", encoding="utf-8") as f:
        for ev in all_negation_events:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    print(f"Logged negation guard events to: {negation_events_path}")

    # Verify TTL & PII Filter
    print("\n" + "=" * 80)
    print("VERIFYING GUARDRAILS (TTL Expiry & PII / Order ID Regex Filter)")
    print("=" * 80)

    # 1. Test PII / Order ID Filter
    test_pii_cases = [
        ("Here is your tracking code: ORD-992384 and password.", True),
        ("Customer Name: Mr. Rajesh Sharma, phone: 9876543210.", True),
        ("Standard delivery typically takes 3 to 5 business days.", False),
    ]
    print("\nTesting PII Filter:")
    for text, should_block in test_pii_cases:
        blocked, matched = contains_pii_or_order_id(text)
        status = "BLOCKED" if blocked else "ALLOWED"
        print(f"  [{status}] Text: '{text[:50]}...' -> Match: {matched}")
        assert blocked == should_block, f"PII check failed for: {text}"

    # 2. Test TTL Expiry
    print("\nTesting TTL Expiry:")
    ttl_cache = SemanticCache(default_ttl_seconds=1.0)
    ttl_cache.add("What is the temporary code?", "The code is 12345.", ttl_seconds=0.5)
    
    # Immediate lookup
    hit_now, _, _, audit_now = ttl_cache.lookup("What is the temporary code?")
    print(f"  Immediate lookup: is_hit={hit_now}, expired={audit_now['ttl_expired']}")
    assert hit_now is True, "Immediate lookup should be a cache hit"

    # Wait for TTL expiration
    time.sleep(0.7)
    hit_later, _, _, audit_later = ttl_cache.lookup("What is the temporary code?")
    print(f"  After 0.7s delay: is_hit={hit_later}, expired={audit_later['ttl_expired']}")
    assert hit_later is False and audit_later["ttl_expired"] is True, "Expired item should be a cache miss"
    print("TTL Expiry verified successfully!")


if __name__ == "__main__":
    run_sweep()
