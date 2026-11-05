"""E-commerce FAQ bot orchestrator with semantic caching and LLM fallback.

Embeds queries, checks FAISS semantic cache with guardrails (negation guard, TTL),
returns cached answer on hit (0 tokens), or calls LLM on miss and saves newly
generated answers into the cache (with PII filter).
"""

import os
import sys
import json
import time
from typing import Any, Dict, List, Optional

# Add repo root to sys.path so we can import llm.py
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import llm
from cache import SemanticCache
from logger import CacheLogger

SYSTEM_PROMPT = (
    "You are a helpful and polite customer support assistant for an e-commerce platform. "
    "Provide clear, concise, and accurate answers to customer questions. If the question is "
    "out of scope or unrelated to online shopping/orders/returns, politely clarify that you "
    "can only assist with store-related inquiries."
)


class FAQBot:
    """Orchestrator combining SemanticCache, guardrails, LLM fallback, and JSONL logging."""

    def __init__(
        self,
        cache: Optional[SemanticCache] = None,
        logger: Optional[CacheLogger] = None,
        faq_file: Optional[str] = None,
        default_threshold: float = 0.85,
        default_ttl_seconds: Optional[float] = 86400.0,
        enable_negation_guard: bool = True,
        enable_pii_filter: bool = True,
    ):
        self.cache = cache or SemanticCache(
            threshold=default_threshold,
            default_ttl_seconds=default_ttl_seconds,
            enable_negation_guard=enable_negation_guard,
            enable_pii_filter=enable_pii_filter,
        )
        self.logger = logger or CacheLogger()
        self.default_threshold = default_threshold

        # Optionally populate with base FAQs
        if faq_file:
            self.load_faqs(faq_file)

    def load_faqs(self, faq_path: str) -> int:
        """Load seed FAQs from a JSON file into the semantic cache."""
        if not os.path.exists(faq_path):
            raise FileNotFoundError(f"FAQ file not found: {faq_path}")

        with open(faq_path, "r", encoding="utf-8") as f:
            faqs: List[Dict[str, str]] = json.load(f)

        count = 0
        for item in faqs:
            success, _ = self.cache.add(
                question=item["question"],
                answer=item["answer"],
                faq_id=item.get("id"),
            )
            if success:
                count += 1
        return count

    def ask(self, question: str, threshold: Optional[float] = None) -> Dict[str, Any]:
        """Process a customer question.

        1. Vector search in semantic cache with guardrails.
        2. On HIT (score >= threshold & passes negation guard): return cached answer immediately.
        3. On MISS: call LLM, store new answer in cache, and return.
        """
        start_time = time.perf_counter()
        cutoff = self.default_threshold if threshold is None else threshold

        # 1. Lookup in semantic cache
        is_hit, similarity, match_data, audit = self.cache.lookup(question, threshold=cutoff)

        if is_hit and match_data:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            matched_id = match_data.get("faq_id", "unknown")
            answer = match_data.get("answer", "")

            # Log HIT event
            self.logger.log(
                question=question,
                status="HIT",
                similarity=similarity,
                latency_ms=latency_ms,
                tokens_in=0,
                tokens_out=0,
                matched_faq_id=matched_id,
            )

            return {
                "question": question,
                "answer": answer,
                "hit": True,
                "similarity": similarity,
                "matched_faq_id": matched_id,
                "tokens_in": 0,
                "tokens_out": 0,
                "latency_ms": latency_ms,
                "source": "cache",
                "audit": audit,
            }

        # 2. Cache MISS -> Call LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]

        llm_response = llm.chat(messages, temperature=0.0, max_tokens=350)
        answer = llm_response.get("text", "").strip()
        tokens_in = llm_response.get("tokens_in", 0)
        tokens_out = llm_response.get("tokens_out", 0)

        # 3. Save new answer into cache (if it passes PII filter)
        new_id = f"gen_{self.cache.size() + 1}"
        cached_success, reason = self.cache.add(question=question, answer=answer, faq_id=new_id)

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Log MISS event
        extra = {"cache_save_status": "saved" if cached_success else reason, "audit": audit}
        self.logger.log(
            question=question,
            status="MISS",
            similarity=similarity,
            latency_ms=latency_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            matched_faq_id=None,
            extra=extra,
        )

        return {
            "question": question,
            "answer": answer,
            "hit": False,
            "similarity": similarity,
            "matched_faq_id": None,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "latency_ms": latency_ms,
            "source": "llm",
            "cached": cached_success,
            "audit": audit,
        }
