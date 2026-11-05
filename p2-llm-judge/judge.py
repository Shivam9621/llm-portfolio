"""LLM-as-a-Judge module with order swapping and rubric-guided evaluation.

Given a question and two candidate answers (A and B), evaluates them at temperature=0
using rubric.md and returns JSON {"winner": "A" | "B" | "tie", "reason": "..."}.
Supports swapping A/B presentation order to audit position bias.
"""

import os
import sys
import json
import re
import argparse
from typing import Any, Dict, Optional

# Ensure repo root is accessible
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import llm


def load_rubric(rubric_path: Optional[str] = None) -> str:
    path = rubric_path or os.path.join(SCRIPT_DIR, "rubric.md")
    api_rubric = os.path.join(REPO_ROOT, "api", "data", "rubric.md")
    if not os.path.exists(path) and os.path.exists(api_rubric):
        path = api_rubric
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Evaluate answers based on Correctness (45%), Completeness (35%), and Clarity (20%)."


def parse_judge_json(raw_text: str) -> Dict[str, Any]:
    """Robust JSON extraction from LLM judge response."""
    raw = raw_text.strip()
    # Strip markdown code blocks if present
    if "```json" in raw:
        match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
        if match:
            raw = match.group(1).strip()
    elif "```" in raw:
        match = re.search(r"```\s*(.*?)\s*```", raw, re.DOTALL)
        if match:
            raw = match.group(1).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback regex extraction if model returned conversational preamble
        winner_match = re.search(r'"winner"\s*:\s*"([12ABtieTIE]+)"', raw, re.IGNORECASE)
        reason_match = re.search(r'"reason"\s*:\s*"(.*?)"', raw, re.DOTALL)
        winner = winner_match.group(1) if winner_match else "tie"
        reason = reason_match.group(1) if reason_match else raw[:200]
        return {"winner": winner, "reason": reason}


def judge_pair(
    question: str,
    answer_a: str,
    answer_b: str,
    swap_order: bool = False,
    rubric_text: Optional[str] = None,
    backend: Optional[str] = None,
    model: Optional[str] = None,
    length_penalty_instruction: bool = False,
) -> Dict[str, Any]:
    """Evaluate two answers using rubric-guided LLM judgment.

    Args:
        question: The user prompt / technical question.
        answer_a: Candidate A answer text.
        answer_b: Candidate B answer text.
        swap_order: If True, presents Answer B as Candidate 1 and Answer A as Candidate 2.
        rubric_text: Text of the evaluation rubric.
        backend: LLM backend override.
        model: LLM model override.
        length_penalty_instruction: Whether to explicitly instruct that length does not matter.

    Returns:
        Dict containing: 'winner' ('A', 'B', or 'tie'), 'reason', 'swap_order', 'raw_choice'
    """
    rubric = rubric_text or load_rubric()

    # Determine presentation order
    if swap_order:
        cand_1 = answer_b
        cand_2 = answer_a
        presentation = "Candidate 1 = Answer B, Candidate 2 = Answer A"
    else:
        cand_1 = answer_a
        cand_2 = answer_b
        presentation = "Candidate 1 = Answer A, Candidate 2 = Answer B"

    extra_instructions = ""
    if length_penalty_instruction:
        extra_instructions = (
            "\nCRITICAL INSTRUCTION: Length and word count do NOT matter. "
            "Do NOT penalize shorter answers or reward longer ones. Focus purely on technical "
            "correctness, accuracy, and insight."
        )

    system_prompt = (
        "You are an impartial, expert technical judge evaluating answers to software engineering questions.\n"
        "Your task is to select the superior answer strictly following this evaluation rubric:\n\n"
        f"{rubric}\n\n"
        f"{extra_instructions}\n"
        "You MUST respond ONLY with a JSON object in this exact format (no markdown, no other text):\n"
        '{"winner": "1" | "2" | "tie", "reason": "<concise explanation>"}'
    )

    user_prompt = (
        f"Question:\n{question}\n\n"
        f"[Candidate 1]:\n{cand_1}\n\n"
        f"[Candidate 2]:\n{cand_2}\n\n"
        "Evaluate Candidate 1 vs Candidate 2. Output your JSON decision:"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    llm_resp = llm.chat(messages, temperature=0.0, max_tokens=300, backend=backend, model=model)
    parsed = parse_judge_json(llm_resp.get("text", ""))

    raw_choice = str(parsed.get("winner", "tie")).strip()
    reason = parsed.get("reason", "").strip()

    # Normalize raw choice
    raw_choice_upper = raw_choice.upper()
    if raw_choice_upper in ("1", "A"):
        raw_choice_norm = "1"
    elif raw_choice_upper in ("2", "B"):
        raw_choice_norm = "2"
    else:
        raw_choice_norm = "tie"

    # Map back to canonical Model A vs Model B
    if raw_choice_norm == "1":
        canonical_winner = "B" if swap_order else "A"
    elif raw_choice_norm == "2":
        canonical_winner = "A" if swap_order else "B"
    else:
        canonical_winner = "tie"

    return {
        "winner": canonical_winner,
        "reason": reason,
        "swap_order": swap_order,
        "presentation": presentation,
        "raw_choice": raw_choice_norm,
        "tokens_in": llm_resp.get("tokens_in", 0),
        "tokens_out": llm_resp.get("tokens_out", 0),
        "latency_ms": llm_resp.get("latency_ms", 0.0),
    }


def evaluate_batch(
    answers_jsonl: str,
    output_jsonl: str,
    swap_order: bool = False,
    backend: Optional[str] = None,
    model: Optional[str] = None,
    length_instruction: bool = False,
):
    rubric = load_rubric()
    results = []

    with open(answers_jsonl, "r", encoding="utf-8") as f:
        pairs = [json.loads(line) for line in f if line.strip()]

    order_label = "SWAPPED (B then A)" if swap_order else "NORMAL (A then B)"
    print(f"Evaluating {len(pairs)} question pairs in {order_label} order...")

    for idx, pair in enumerate(pairs, 1):
        qid = pair["id"]
        q = pair["question"]
        ans_a = pair["answer_a"]
        ans_b = pair["answer_b"]

        print(f"[{idx}/{len(pairs)}] Judging {qid}...")
        decision = judge_pair(
            question=q,
            answer_a=ans_a,
            answer_b=ans_b,
            swap_order=swap_order,
            rubric_text=rubric,
            backend=backend,
            model=model,
            length_penalty_instruction=length_instruction,
        )
        record = {
            "id": qid,
            "question": q,
            "winner": decision["winner"],
            "raw_choice": decision["raw_choice"],
            "reason": decision["reason"],
            "swap_order": swap_order,
            "latency_ms": decision["latency_ms"],
        }
        results.append(record)

    os.makedirs(os.path.dirname(os.path.abspath(output_jsonl)), exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Saved {len(results)} verdicts to: {output_jsonl}")


def main():
    parser = argparse.ArgumentParser(description="LLM Judge for answer pair evaluation")
    parser.add_argument("--answers", default=os.path.join(SCRIPT_DIR, "answers.jsonl"))
    parser.add_argument("--output", default=None)
    parser.add_argument("--swap", action="store_true", help="Swap presentation order (present B then A)")
    parser.add_argument("--length-instruction", action="store_true", help="Inject 'length does not matter' rule")
    parser.add_argument("--backend", default=None)
    parser.add_argument("--model", default=None)

    args = parser.parse_args()

    default_out_name = "judge_verdicts_swapped.jsonl" if args.swap else "judge_verdicts_normal.jsonl"
    out_path = args.output or os.path.join(REPO_ROOT, "results", default_out_name)

    evaluate_batch(
        answers_jsonl=args.answers,
        output_jsonl=out_path,
        swap_order=args.swap,
        backend=args.backend,
        model=args.model,
        length_instruction=args.length_instruction,
    )


if __name__ == "__main__":
    main()
