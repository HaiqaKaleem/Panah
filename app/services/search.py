"""Full-text search engine across all PANAGAH entities."""

import re
import sqlite3
from typing import Any, Optional
from dataclasses import dataclass, field

from fastapi import APIRouter, Query

router = APIRouter(prefix="/search", tags=["Search"])


@dataclass
class SearchResult:
    """Single search result."""
    entity_type: str
    entity_id: str
    title: str
    snippet: str
    score: float
    metadata: dict = field(default_factory=dict)


class SearchEngine:
    """In-memory full-text search engine with ranking."""

    def __init__(self):
        self._index: dict[str, list[dict]] = {}
        self._stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "shall", "can", "need", "dare", "ought",
            "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "above", "below",
            "between", "out", "off", "over", "under", "again", "further", "then",
            "once", "here", "there", "when", "where", "why", "how", "all", "each",
            "every", "both", "few", "more", "most", "other", "some", "such", "no",
            "not", "only", "own", "same", "so", "than", "too", "very", "just",
            "and", "but", "or", "if", "this", "that", "these", "those", "it", "its",
        }

    def index_entity(self, entity_type: str, entity_id: str, fields: dict[str, str],
                     metadata: Optional[dict] = None):
        """Index an entity with searchable fields."""
        for field_name, text in fields.items():
            if text:
                tokens = self._tokenize(text)
                for token in tokens:
                    key = f"{entity_type}:{token}"
                    if key not in self._index:
                        self._index[key] = []
                    self._index[key].append({
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "field": field_name,
                        "text": text,
                        "metadata": metadata or {},
                    })

    def search(self, query: str, entity_types: Optional[list[str]] = None,
               limit: int = 20) -> list[SearchResult]:
        """Search across all indexed entities with TF-IDF-like scoring."""
        tokens = self._tokenize(query)
        if not tokens:
            return []

        scores: dict[str, float] = {}
        details: dict[str, dict] = {}

        for token in tokens:
            for entity_type in ["project", "site", "material", "design", "constraint",
                                "review", "validation", "observation"]:
                key = f"{entity_type}:{token}"
                if key in self._index:
                    for entry in self._index[key]:
                        if entity_types and entry["entity_type"] not in entity_types:
                            continue
                        doc_id = f"{entry['entity_type']}:{entry['entity_id']}"
                        # TF-IDF-like scoring
                        tf = entry["text"].lower().count(token) / max(len(entry["text"].split()), 1)
                        scores[doc_id] = scores.get(doc_id, 0) + tf * 2.0
                        if doc_id not in details:
                            details[doc_id] = entry

        # Sort by score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]

        results = []
        for doc_id, score in ranked:
            entry = details[doc_id]
            snippet = self._extract_snippet(entry["text"], query)
            results.append(SearchResult(
                entity_type=entry["entity_type"],
                entity_id=entry["entity_id"],
                title=entry["metadata"].get("name", entry["entity_id"]),
                snippet=snippet,
                score=round(score, 3),
                metadata=entry["metadata"],
            ))

        return results

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into searchable tokens."""
        text = text.lower()
        tokens = re.findall(r"[a-z0-9\u0600-\u06ff]+", text)  # Support Arabic/Urdu
        return [t for t in tokens if t not in self._stopwords and len(t) > 1]

    def _extract_snippet(self, text: str, query: str, context_chars: int = 100) -> str:
        """Extract relevant snippet around match."""
        text_lower = text.lower()
        for word in query.lower().split():
            idx = text_lower.find(word.lower())
            if idx >= 0:
                start = max(0, idx - context_chars)
                end = min(len(text), idx + len(word) + context_chars)
                snippet = text[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."
                return snippet
        return text[:200]


# Global search engine instance
search_engine = SearchEngine()


# ── API Endpoints ─────────────────────────────────────────────────────

@router.get("", summary="Full-text search across all entities")
async def search_all(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    types: Optional[str] = Query(None, description="Comma-separated entity types to search"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
):
    """
    Full-text search across projects, sites, materials, designs, and more.

    Supports English, Urdu, and Arabic text. Results are ranked by relevance.
    """
    entity_types = types.split(",") if types else None
    results = search_engine.search(q, entity_types=entity_types, limit=limit)

    return {
        "query": q,
        "total": len(results),
        "results": [
            {
                "type": r.entity_type,
                "id": r.entity_id,
                "title": r.title,
                "snippet": r.snippet,
                "score": r.score,
                "metadata": r.metadata,
            }
            for r in results
        ],
    }


@router.get("/suggest", summary="Search suggestions / autocomplete")
async def search_suggest(
    q: str = Query(..., min_length=1, max_length=50),
    limit: int = Query(5, ge=1, le=20),
):
    """Get search suggestions based on partial input."""
    results = search_engine.search(q, limit=limit)
    return {
        "suggestions": [
            {"text": r.title, "type": r.entity_type}
            for r in results
        ],
    }
