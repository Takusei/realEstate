# rag_retrieval.py
from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import vertexai
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

# ----------------------------
# Vertex AI Embeddings (init)
# ----------------------------
vertexai.init(
    project=os.getenv("PROJECT_ID", "dev-projects-476011"),
    location=os.getenv("LOCATION", "asia-northeast1"),
)
EMB = TextEmbeddingModel.from_pretrained("text-multilingual-embedding-002")


def embed_query(text: str) -> List[float]:
    """Return a 768-dim embedding for the query (or [] if blank)."""
    if not text or not text.strip():
        return []
    # Trim to safe size; VertexAI allows long, but keep practical.
    return EMB.get_embeddings([TextEmbeddingInput(text[:7000])])[0].values


# ---------------------------------------------------------
# Filters: split into (1) vectorSearch-safe and (2) post-$match
# ---------------------------------------------------------
# Why split?
# - $vectorSearch.filter only supports standard MQL. It’s safest to include:
#   - equals/scalar, booleans, numeric ranges, $in
# - Keep regex / complex expressions for a post-$match stage, after $vectorSearch.
#   (Regex on Japanese text often needs to run post-vector to avoid 0 results.)
#
# Input: mongo_filter like {"$and":[{"price_yen":{"$lte":50000000}}, {"address":{"$regex":"目黒区"}}]}
# Output:
#   vs_filter: {"$and":[{"price_yen":{"$lte":50000000}}]}        # goes inside $vectorSearch.filter
#   post_match: {"$and":[{"address":{"$regex":"目黒区"}}]}        # separate $match after $vectorSearch
#
def _split_filters_for_vectorsearch(
    mongo_filter: Dict[str, Any],
) -> Tuple[Dict[str, Any] | None, Dict[str, Any] | None]:
    def _is_range_dict(d: Dict[str, Any]) -> bool:
        return any(k in d for k in ("$gte", "$lte", "$gt", "$lt"))

    if not mongo_filter or "$and" not in mongo_filter:
        return None, None

    vs_and: List[Dict[str, Any]] = []
    post_and: List[Dict[str, Any]] = []

    for condition in mongo_filter["$and"]:
        if not isinstance(condition, dict) or not condition:
            continue
        field, expr = list(condition.items())[0]

        # Direct booleans/scalars
        if isinstance(expr, (bool, int, float, str)):
            # For $vectorSearch.filter, equality on scalar is fine.
            vs_and.append({field: expr})
            continue

        # Dict operators
        if isinstance(expr, dict):
            # Numeric/standard ranges
            if _is_range_dict(expr):
                rng: Dict[str, Any] = {}
                # Only keep non-None bounds
                for op in ("$gte", "$lte", "$gt", "$lt"):
                    if expr.get(op) is not None:
                        rng[op] = expr[op]
                if rng:
                    vs_and.append({field: rng})
                continue

            # $in is safe for vs-filter
            if "$in" in expr and isinstance(expr["$in"], list):
                vs_and.append({field: {"$in": expr["$in"]}})
                continue

            # $eq is safe
            if "$eq" in expr:
                vs_and.append({field: {"$eq": expr["$eq"]}})
                continue

            # $regex and anything else unknown -> post-match
            # (Regex support in $vectorSearch.filter is inconsistent; keep it post-stage.)
            post_and.append({field: expr})
            continue

        # Fallback: unknown shape -> post-match
        post_and.append({field: expr})

    vs_filter = {"$and": vs_and} if vs_and else None
    post_match = {"$and": post_and} if post_and else None
    return vs_filter, post_match


# -----------------------------------------
# Main retrieval with $vectorSearch
# -----------------------------------------
def retrieve_semantic(
    PROPS,  # pymongo collection
    query_text: str,
    filters: Dict[str, Any],
    k: int = 300,
    limit: int = 30,
    index: str = "rec_index",  # <-- your vectorSearch index name
    num_candidates: int = 6000,
) -> List[dict]:
    """
    Vector-first retriever:
      - If query_text is present -> $vectorSearch using queryVector
      - Safe prefilters (ranges/equals/booleans/$in) go into $vectorSearch.filter
      - Regex/complex bits go into a post $match stage
      - Projects vector score via $meta: 'vectorSearchScore'
    Fallback when no query_text: pure $match + $limit.
    """
    qvec = embed_query(query_text)
    mongo_match_filter = _safe_build_match(
        filters
    )  # wraps your existing build_match() safely
    vs_filter, post_match = _split_filters_for_vectorsearch(mongo_match_filter)

    pipeline: List[Dict[str, Any]] = []

    if qvec:
        # $vectorSearch (limit is part of this stage)
        vs_stage: Dict[str, Any] = {
            "$vectorSearch": {
                "index": index,
                "path": "embedding",
                "queryVector": qvec,
                "numCandidates": max(num_candidates, k),
                "limit": max(1, limit),
            }
        }
        if vs_filter:
            vs_stage["$vectorSearch"]["filter"] = vs_filter
        pipeline.append(vs_stage)

        # Post-filter text/regex/etc. *after* vector stage
        if post_match:
            pipeline.append({"$match": post_match})

        # Projection with vectorSearchScore
        pipeline.append(
            {
                "$project": {
                    "name": 1,
                    "address": 1,
                    "image": 1,
                    "url": 1,
                    "price_yen": 1,
                    "area_sqm": 1,
                    "rooms": 1,
                    "layout_raw": 1,
                    "size": 1,
                    "station_line": 1,
                    "station_name": 1,
                    "station_walk_minutes": 1,
                    "flags": 1,
                    "description": 1,
                    "vector_score": {"$meta": "vectorSearchScore"},
                }
            }
        )
    else:
        print("No query vector provided; falling back to pure MQL filtering.")
        # No query: pure MQL filtering; still honor all conditions
        if mongo_match_filter:
            pipeline.append({"$match": mongo_match_filter})
        # If nothing provided, just ensure documents with embeddings come first (optional)
        pipeline.extend(
            [
                {"$limit": max(1, limit)},
                {
                    "$project": {
                        "name": 1,
                        "address": 1,
                        "image": 1,
                        "url": 1,
                        "price_yen": 1,
                        "area_sqm": 1,
                        "rooms": 1,
                        "layout_raw": 1,
                        "size": 1,
                        "station_line": 1,
                        "station_name": 1,
                        "station_walk_minutes": 1,
                        "flags": 1,
                        "description": 1,
                        # No vector score without $vectorSearch
                        "vector_score": {"$literal": None},
                    }
                },
            ]
        )

    out = list(PROPS.aggregate(pipeline))
    if not out:
        print(
            {
                "debug": "empty_results",
                "has_qvec": bool(qvec),
                "index": index,
                "k": k,
                "numCandidates": num_candidates,
                "limit": limit,
                "vs_filter": vs_filter,
                "post_match": post_match,
            }
        )
    return out


# -----------------------------------------
# Safe wrapper around your rec_core.build_match
# -----------------------------------------
def _safe_build_match(user_filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call your existing build_match(filters) and normalize into {"$and":[...]} with only valid entries.
    Removes empty/None-ish conditions early to avoid accidental zero-results.
    """
    try:
        # You already have this in your project
        from rec_core import build_match  # type: ignore
    except Exception:
        build_match = None

    raw = {}
    if callable(build_match):
        try:
            raw = build_match(user_filters) or {}
        except Exception as e:
            print(f"[build_match] error: {e}")
            raw = {}

    # Normalize to "$and"
    if not raw:
        return {}
    if "$and" not in raw:
        # Convert {field: expr, field2: expr2} into {"$and":[{field:expr},{field2:expr2}]}
        if isinstance(raw, dict):
            and_list = []
            for k, v in raw.items():
                if v is None or (isinstance(v, dict) and len(v) == 0):
                    continue
                and_list.append({k: v})
            return {"$and": and_list} if and_list else {}
        return {}

    # Clean out empty conditions
    and_clean = []
    for cond in raw.get("$and", []):
        if isinstance(cond, dict) and cond:
            field, expr = list(cond.items())[0]
            if expr is None:
                continue
            if isinstance(expr, dict) and not expr:
                continue
            and_clean.append({field: expr})
    return {"$and": and_clean} if and_clean else {}
