# embed_batch_genai.py
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import pymongo
from google import genai
from google.genai import types
from search_text import build_search_text

# ---------------------------
# Config
# ---------------------------
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("GOOGLE_LOCATION", "asia-northeast1")

DB_NAME = os.getenv("DB_NAME", "suumo")
COLL = os.getenv("MONGO_COLLECTION_NAME", "suumo")
MONGO_URI = os.environ["MONGO_URI"]

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-multilingual-embedding-002")
BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "64"))
EMBED_MAX_WORKERS = int(os.getenv("EMBED_MAX_WORKERS", "8"))
EMBED_TASK_TYPE = os.getenv(
    "EMBED_TASK_TYPE", "RETRIEVAL_DOCUMENT"
)  # or RETRIEVAL_QUERY

# ---------------------------
# Client (Vertex routing)
# ---------------------------
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)


# ---------------------------
# Helpers
# ---------------------------
def _extract_embedding_any(resp) -> List[float]:
    """
    Normalize different response shapes into a single embedding vector.
    Handles:
      - Batch: resp.embeddings -> [Embedding], resp.responses -> [Embedding], or list
      - Single: resp.embedding (Embedding) or Embedding
      - Dict-ish responses
    """
    # Batch-like: list of embeddings
    if isinstance(resp, list) and resp:
        obj = resp[0]
        if hasattr(obj, "values"):
            return list(obj.values)
        if isinstance(obj, dict) and "values" in obj:
            return list(obj["values"])

    # Batch object with `.embeddings`
    if hasattr(resp, "embeddings") and resp.embeddings:
        obj = resp.embeddings[0]
        if hasattr(obj, "values"):
            return list(obj.values)

    # Batch object with `.responses`
    if hasattr(resp, "responses") and resp.responses:
        obj = resp.responses[0]
        # Some SDKs keep the Embedding under `.embedding`
        if hasattr(obj, "embedding") and hasattr(obj.embedding, "values"):
            return list(obj.embedding.values)
        if hasattr(obj, "values"):
            return list(obj.values)

    # Single object with `.embedding`
    if hasattr(resp, "embedding") and hasattr(resp.embedding, "values"):
        return list(resp.embedding.values)

    # Single object is itself an Embedding
    if hasattr(resp, "values"):
        return list(resp.values)

    # Dict fallbacks
    if isinstance(resp, dict):
        if (
            "embedding" in resp
            and isinstance(resp["embedding"], dict)
            and "values" in resp["embedding"]
        ):
            return list(resp["embedding"]["values"])
        if "values" in resp:
            return list(resp["values"])

    raise ValueError(f"Unrecognized embedding response shape: {type(resp)} -> {resp}")


def _embed_single(text: str, retries: int = 3, backoff: float = 0.7) -> List[float]:
    """
    Embed one string. Tries multiple call signatures for broad SDK compatibility.
    Returns [] on failure (keeps position alignment).
    """
    for attempt in range(retries):
        try:
            cfg = types.EmbedContentConfig(task_type=EMBED_TASK_TYPE)

            # Prefer the most common newer signature: contents=[str]
            if hasattr(client.models, "embed_content"):
                try:
                    resp = client.models.embed_content(
                        model=EMBED_MODEL,
                        contents=[text],  # <-- note: contents (list)
                        config=cfg,
                    )
                    return _extract_embedding_any(resp)
                except TypeError:
                    # Some builds want `content=` (single string)
                    resp = client.models.embed_content(
                        model=EMBED_MODEL,
                        content=text,  # <-- single string
                        config=cfg,
                    )
                    return _extract_embedding_any(resp)

            # Older/alternate method name: embed(...)
            if hasattr(client.models, "embed"):
                try:
                    resp = client.models.embed(
                        model=EMBED_MODEL,
                        contents=[text],
                        config=cfg,
                    )
                    return _extract_embedding_any(resp)
                except TypeError:
                    resp = client.models.embed(
                        model=EMBED_MODEL,
                        content=text,
                        config=cfg,
                    )
                    return _extract_embedding_any(resp)

            # Very old namespace: client.embeddings.embed_content(...)
            if hasattr(client, "embeddings") and hasattr(
                client.embeddings, "embed_content"
            ):
                try:
                    resp = client.embeddings.embed_content(
                        model=EMBED_MODEL,
                        contents=[text],
                        config=cfg,
                    )
                    return _extract_embedding_any(resp)
                except TypeError:
                    resp = client.embeddings.embed_content(
                        model=EMBED_MODEL,
                        content=text,
                        config=cfg,
                    )
                    return _extract_embedding_any(resp)

            # If we reach here, the installed SDK is unexpected
            raise AttributeError(
                "No compatible embed method found on this google-genai version."
            )

        except Exception as e:
            if attempt == retries - 1:
                print(f"[embed_single] failed after {retries} attempts: {e}")
                return []
            time.sleep(backoff * (2**attempt))

    return []


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Returns one embedding vector per input text.
    - If batch API exists in the installed SDK, use it.
    - Otherwise, do parallel single calls with retries.
    """
    cfg = types.EmbedContentConfig(task_type=EMBED_TASK_TYPE)

    # Try batch if available
    if hasattr(client.models, "batch_embed_contents"):
        try:
            # Many builds accept list[str] directly under `contents`
            resp = client.models.batch_embed_contents(
                model=EMBED_MODEL,
                contents=texts,
                config=cfg,
            )
            # Normalize batch response
            if hasattr(resp, "embeddings") and resp.embeddings:
                return [list(e.values) for e in resp.embeddings]
            if hasattr(resp, "responses") and resp.responses:
                out = []
                for r in resp.responses:
                    out.append(_extract_embedding_any(r))
                return out
            if isinstance(resp, list):
                return [_extract_embedding_any(r) for r in resp]
            print("[embed_texts] batch returned no embeddings; falling back.")
        except Exception as e:
            print(f"[embed_texts] batch_embed_contents failed; falling back: {e}")

    # Fallback: parallel single calls (works across all known versions)
    out = [None] * len(texts)

    def work(ix_text):
        ix, t = ix_text
        out[ix] = _embed_single(t)

    with ThreadPoolExecutor(max_workers=EMBED_MAX_WORKERS) as ex:
        futures = [ex.submit(work, (i, t)) for i, t in enumerate(texts)]
        for _ in as_completed(futures):
            pass

    # Replace any None with [] (shouldn't happen)
    return [v if isinstance(v, list) else [] for v in out]


# ---------------------------
# Main ETL
# ---------------------------
def main():
    mongo = pymongo.MongoClient(MONGO_URI)
    col = mongo[DB_NAME][COLL]

    cur = col.find(
        {"$or": [{"embedding": {"$exists": False}}, {"embedding": None}]},
        {
            "_id": 1,
            "name": 1,
            "description": 1,
            "category": 1,
            "address": 1,
            "station_line": 1,
            "station_name": 1,
            "layout_raw": 1,
            "size": 1,
            "flags": 1,
        },
    ).batch_size(200)

    batch_ids, batch_txts = [], []

    def flush_batch():
        nonlocal batch_ids, batch_txts
        if not batch_txts:
            print("No texts to embed in this batch.")
            return
        print(f"Embedding batch of {len(batch_txts)} items...")
        vecs = embed_texts(batch_txts)
        for _id, v in zip(batch_ids, vecs):
            if v:  # only update if embedding succeeded
                col.update_one({"_id": _id}, {"$set": {"embedding": v}})
        batch_ids, batch_txts = [], []

    for d in cur:
        batch_ids.append(d["_id"])
        # Safety truncation (avoid overlong inputs)
        batch_txts.append(build_search_text(d)[:7000])
        if len(batch_txts) >= BATCH_SIZE:
            flush_batch()

    flush_batch()


if __name__ == "__main__":
    main()
