"""Command-line interface for the Semantic Cache FAQ Bot."""

import os
import sys
import argparse

# Ensure local imports work cleanly
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from bot import FAQBot


def print_response(res: dict) -> None:
    source_tag = "[CACHE HIT]" if res["hit"] else "[LLM GENERATED (MISS)]"
    color = "\033[92m" if res["hit"] else "\033[93m"
    reset = "\033[0m"

    print("\n" + "=" * 60)
    print(f"Status:        {color}{source_tag}{reset}")
    if res["hit"]:
        print(f"Matched FAQ:   {res['matched_faq_id']}")
    print(f"Similarity:    {res['similarity']:.4f}")
    print(f"Latency:       {res['latency_ms']:.2f} ms")
    print(f"Tokens Used:   in={res['tokens_in']}, out={res['tokens_out']}")
    print("-" * 60)
    print(f"Answer:\n{res['answer']}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="E-commerce FAQ Bot with Semantic Cache")
    parser.add_argument("--ask", type=str, help="Single question to query")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive chat REPL")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Similarity threshold for cache hits (0.0 to 1.0, default: 0.85)",
    )
    parser.add_argument(
        "--faqs",
        type=str,
        default=os.path.join(SCRIPT_DIR, "faqs.json"),
        help="Path to faqs.json seed file",
    )

    args = parser.parse_args()

    print(f"Initializing Semantic Cache FAQ Bot (Threshold: {args.threshold})...")
    bot = FAQBot(faq_file=args.faqs, default_threshold=args.threshold)
    print(f"Loaded {bot.cache.size()} FAQs into vector cache.")

    if args.ask:
        response = bot.ask(args.ask, threshold=args.threshold)
        print_response(response)
        return

    if args.interactive or not args.ask:
        print("\nInteractive FAQ Bot Shell. Type 'exit' or 'quit' to stop.\n")
        while True:
            try:
                user_input = input("faq-bot> ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("exit", "quit", "q"):
                    print("Exiting. Goodbye!")
                    break
                response = bot.ask(user_input, threshold=args.threshold)
                print_response(response)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting. Goodbye!")
                break


if __name__ == "__main__":
    main()
