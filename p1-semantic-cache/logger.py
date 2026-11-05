"""JSONL logger for semantic cache events and metrics."""

import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class CacheLogger:
    """Thread-safe / append-only JSONL logger for cache hit/miss queries."""

    def __init__(self, log_path: Optional[str] = None):
        if log_path is None:
            # Default to results/p1_cache_log.jsonl at the repo root
            repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            results_dir = os.path.join(repo_root, "results")
            os.makedirs(results_dir, exist_ok=True)
            self.log_path = os.path.join(results_dir, "p1_cache_log.jsonl")
        else:
            os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
            self.log_path = log_path

    def log(
        self,
        question: str,
        status: str,
        similarity: float,
        latency_ms: float,
        tokens_in: int,
        tokens_out: int,
        matched_faq_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record an event to the JSONL log file."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": question,
            "status": status.upper(),  # 'HIT' or 'MISS'
            "similarity": round(float(similarity), 4),
            "matched_faq_id": matched_faq_id,
            "latency_ms": round(float(latency_ms), 2),
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out),
            "total_tokens": int(tokens_in) + int(tokens_out),
        }
        if extra:
            entry.update(extra)

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return entry
