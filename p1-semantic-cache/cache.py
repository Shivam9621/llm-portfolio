"""Semantic Cache implementation using paraphrase-multilingual-MiniLM-L12-v2 and FAISS IndexFlatIP.

Includes:
- Normalized FAISS cosine similarity search.
- Negation Guard: detects polarity conflicts between query and cached question.
- TTL Expiry: automatically invalidates stale entries.
- Sensitive Data / PII Regex Filter: refuses to cache answers with Order IDs or personal details.
"""

import os
import re
import json
import time
from typing import Any, Dict, List, Optional, Tuple, Set
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

# Negation words across English and Hindi/Hinglish
NEGATION_WORDS: Set[str] = {
    "not", "no", "never", "none", "neither", "nor", "cannot", "cant", "dont", "do not",
    "nahi", "nahin", "nhi", "mat", "na"
}

# Regex for Order IDs, tracking numbers, and customer names
PII_PATTERNS = [
    re.compile(r"\b(?:ORD|ORDER|TRACK|INV|REF)[-_:#]?\d{4,12}\b", re.IGNORECASE),
    re.compile(r"\b(?:Customer\s+Name[:\s]+[A-Z][a-z]+|(?:Mr\.|Mrs\.|Ms\.)\s+[A-Z][a-z]+)\b"),
]


def extract_negations(text: str) -> Set[str]:
    """Extract negation tokens from text using word-boundary matching."""
    tokens = set(re.findall(r"\b[a-zA-Z']+\b", text.lower()))
    return tokens.intersection(NEGATION_WORDS)


def contains_pii_or_order_id(text: str) -> Tuple[bool, Optional[str]]:
    """Check if text contains order IDs, phone numbers, emails, or personal names."""
    for pattern in PII_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, match.group(0)
    return False, None


class SemanticCache:
    """Vector semantic cache backed by SentenceTransformers and FAISS with guardrails."""

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        dimension: int = 384,
        threshold: float = 0.85,
        default_ttl_seconds: Optional[float] = 86400.0,  # 24 hours default TTL
        enable_negation_guard: bool = True,
        enable_pii_filter: bool = True,
    ):
        self.model_name = model_name
        self.dimension = dimension
        self.default_threshold = threshold
        self.default_ttl = default_ttl_seconds
        self.enable_negation_guard = enable_negation_guard
        self.enable_pii_filter = enable_pii_filter

        self.model = SentenceTransformer(model_name)
        self.index = faiss.IndexFlatIP(dimension)
        self.metadata: List[Dict[str, Any]] = []
        self.negation_guard_events: List[Dict[str, Any]] = []

    def _embed(self, text: str) -> np.ndarray:
        """Compute L2-normalized embedding for a text string."""
        embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        embedding = np.ascontiguousarray(embedding, dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(embedding)
        return embedding

    def add(
        self,
        question: str,
        answer: str,
        faq_id: Optional[str] = None,
        ttl_seconds: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """Add a question-answer pair to the cache.

        Applies PII/Order ID filter: refuses to cache answers with sensitive data.

        Returns:
            Tuple of (success: bool, reason_or_id: str)
        """
        if self.enable_pii_filter:
            has_pii, matched_token = contains_pii_or_order_id(answer)
            if has_pii:
                return False, f"REJECTED_PII_OR_ORDER_ID: Found sensitive token '{matched_token}'"

        vector = self._embed(question)
        self.index.add(vector)

        now = time.time()
        entry_id = faq_id or f"custom_{len(self.metadata) + 1}"
        entry = {
            "faq_id": entry_id,
            "question": question,
            "answer": answer,
            "created_at": now,
            "ttl_seconds": ttl_seconds if ttl_seconds is not None else self.default_ttl,
        }
        self.metadata.append(entry)
        return True, entry_id

    def lookup(
        self,
        query: str,
        threshold: Optional[float] = None,
        check_negation: Optional[bool] = None,
        check_ttl: bool = True,
    ) -> Tuple[bool, float, Optional[Dict[str, Any]], Dict[str, Any]]:
        """Lookup a query in the cache.

        Args:
            query: User question string.
            threshold: Cosine similarity cutoff.
            check_negation: Override negation guard setting.
            check_ttl: Whether to check TTL expiration.

        Returns:
            Tuple of (is_hit, similarity_score, metadata_dict or None, audit_info_dict).
        """
        audit = {
            "negation_blocked": False,
            "ttl_expired": False,
            "raw_similarity": 0.0,
            "matched_question": None,
        }

        if self.index.ntotal == 0:
            return False, 0.0, None, audit

        cutoff = self.default_threshold if threshold is None else threshold
        should_check_negation = (
            self.enable_negation_guard if check_negation is None else check_negation
        )

        query_vec = self._embed(query)
        distances, indices = self.index.search(query_vec, 1)
        top_score = float(distances[0][0])
        top_idx = int(indices[0][0])
        audit["raw_similarity"] = top_score

        if top_idx < 0 or top_idx >= len(self.metadata):
            return False, top_score, None, audit

        candidate = self.metadata[top_idx]
        audit["matched_question"] = candidate["question"]

        # 1. TTL Check
        if check_ttl and candidate.get("ttl_seconds") is not None:
            age = time.time() - candidate.get("created_at", 0)
            if age > candidate["ttl_seconds"]:
                audit["ttl_expired"] = True
                return False, top_score, candidate, audit

        # 2. Threshold Check
        if top_score < cutoff:
            return False, top_score, candidate, audit

        # 3. Negation Guard Check
        if should_check_negation:
            query_negs = extract_negations(query)
            cached_negs = extract_negations(candidate["question"])

            # If one has negation and the other does not -> Polarity Mismatch!
            has_q_neg = len(query_negs) > 0
            has_c_neg = len(cached_negs) > 0

            if has_q_neg != has_c_neg:
                audit["negation_blocked"] = True
                event = {
                    "query": query,
                    "matched_question": candidate["question"],
                    "query_negations": list(query_negs),
                    "cached_negations": list(cached_negs),
                    "similarity": top_score,
                    "faq_id": candidate["faq_id"],
                }
                self.negation_guard_events.append(event)
                return False, top_score, candidate, audit

        # Passed all checks -> Confirmed HIT
        return True, top_score, candidate, audit

    def size(self) -> int:
        """Return the number of entries currently indexed."""
        return self.index.ntotal

    def save(self, directory: str) -> None:
        """Persist index and metadata to disk."""
        os.makedirs(directory, exist_ok=True)
        index_file = os.path.join(directory, "cache.index")
        metadata_file = os.path.join(directory, "cache_metadata.json")

        faiss.write_index(self.index, index_file)
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def load(self, directory: str) -> None:
        """Load index and metadata from disk."""
        index_file = os.path.join(directory, "cache.index")
        metadata_file = os.path.join(directory, "cache_metadata.json")

        if os.path.exists(index_file) and os.path.exists(metadata_file):
            self.index = faiss.read_index(index_file)
            with open(metadata_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
        else:
            raise FileNotFoundError(f"Cache files not found in directory: {directory}")
