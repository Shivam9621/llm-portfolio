"""Demo script showcasing Semantic Caching in action.

Asks questions in three distinct ways:
1. Exact match against an existing FAQ (Instant Cache Hit)
2. Semantic paraphrase of an existing FAQ (Semantic Cache Hit via FAISS)
3. Novel question (Cache Miss -> LLM Call -> Dynamic Cache Save -> Instant Hit on Repeat)
"""

import os
import sys

# Ensure local imports work
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from bot import FAQBot


def print_step(title: str, query: str, res: dict):
    hit_tag = "\033[92m[CACHE HIT]\033[0m" if res["hit"] else "\033[93m[LLM MISS]\033[0m"
    print("\n" + "=" * 70)
    print(f"STEP: {title}")
    print(f"Query:        '{query}'")
    print(f"Outcome:      {hit_tag}")
    if res["hit"]:
        print(f"Matched FAQ:  {res.get('matched_faq_id')}")
    print(f"Similarity:   {res.get('similarity', 0.0):.4f}")
    print(f"Latency:      {res.get('latency_ms'):.2f} ms")
    print(f"Tokens:       in={res.get('tokens_in')}, out={res.get('tokens_out')}")
    print(f"Answer:\n  \"{res.get('answer')[:120]}...\"")
    print("=" * 70)


def main():
    faq_file = os.path.join(SCRIPT_DIR, "faqs.json")
    threshold = 0.75

    print(f"\nInitializing FAQ Bot with Semantic Cache (Threshold={threshold})...")
    bot = FAQBot(faq_file=faq_file, default_threshold=threshold)
    print(f"Seeded {bot.cache.size()} canonical FAQs into FAISS vector cache.")

    # 1. Exact canonical query
    q1 = "What is your return policy?"
    r1 = bot.ask(q1, threshold=threshold)
    print_step("1. Exact Match against Seed FAQ", q1, r1)

    # 2. Semantic Paraphrase Query (hits semantic cache without exact string match)
    q2 = "How do I contact customer support representatives?"
    r2 = bot.ask(q2, threshold=threshold)
    print_step("2. Semantic Paraphrase Query (Cache Hit)", q2, r2)

    # 3. Novel query (misses cache, queries LLM, saves result)
    q3 = "Can I request a phone callback from your customer relationship team?"
    r3 = bot.ask(q3, threshold=threshold)
    print_step("3. Novel Unseen Query (Cold Cache Miss)", q3, r3)

    # 4. Repeat query of previously missed question
    q4 = "Can I request a phone callback from your customer relationship team?"
    r4 = bot.ask(q4, threshold=threshold)
    print_step("4. Repeated Query (Now a Warm Cache Hit)", q4, r4)

    print("\n" + "#" * 70)
    print("PERFORMANCE SUMMARY:")
    print(f"  Cold LLM Call Latency:       {r3['latency_ms']:.2f} ms | Tokens: {r3['tokens_in'] + r3['tokens_out']}")
    print(f"  Warm Cache Hit Latency:      {r4['latency_ms']:.2f} ms | Tokens: 0")
    if r3['latency_ms'] > 0:
        speedup = (r3['latency_ms'] - r4['latency_ms']) / r3['latency_ms'] * 100
        print(f"  Latency Reduction:           {speedup:.1f}% faster")
    print("#" * 70 + "\n")


if __name__ == "__main__":
    main()
