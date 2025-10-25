# embed_batch_genai.py
import os
from typing import List

import pymongo
from google import genai
from google.genai import types
from search_text import build_search_text

# --- Config ---
PROJECT_ID = os.getenv("PROJECT_ID")
DB_NAME = os.getenv("DB_NAME", "suumo")
COLL = os.getenv("MONGO_COLLECTION_NAME", "suumo")
LOCATION = os.getenv("GOOGLE_LOCATION", "asia-northeast1")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-005")
BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "64"))
MONGO_URI = os.environ["MONGO_URI"]

# --- Google GenAI client (Vertex mode) ---
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)


# --- Helpers ---
def _make_embed_req(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part.from_text(text)])


def _extract_embedding(obj) -> List[float]:
    """Extract embedding vector safely across SDK shapes."""
    if hasattr(obj, "values"):
        return list(obj.values)
    if hasattr(obj, "embedding") and hasattr(obj.embedding, "values"):
        return list(obj.embedding.values)
    if isinstance(obj, dict):
        if "values" in obj:
            return list(obj["values"])
        if "embedding" in obj and "values" in obj["embedding"]:
            return list(obj["embedding"]["values"])
    raise ValueError(f"Cannot extract embedding from object: {obj}")


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Batch embed text using text-embedding-005.
    Falls back to per-text embedding if batch fails.
    """
    try:
        # 🧠 Batch API (fast & cheaper)
        response = client.models.batch_embed_contents(
            model=EMBED_MODEL,
            contents=[_make_embed_req(t) for t in texts],
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        return [_extract_embedding(e) for e in response.embeddings]

    except Exception as e:
        print(
            f"[embed_texts] batch_embed_contents failed, fallback to single calls: {e}"
        )

    vectors = []
    for t in texts:
        try:
            r = client.models.embed_content(
                model=EMBED_MODEL,
                content=_make_embed_req(t),
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
            )
            vectors.append(_extract_embedding(r.embedding))
        except Exception as e2:
            print(f"[embed_texts] single embed failed: {e2}")
            vectors.append([])
    return vectors


# --- Main ETL ---
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
            return
        vecs = embed_texts(batch_txts)
        for _id, v in zip(batch_ids, vecs):
            if v:  # only update if embedding succeeded
                col.update_one({"_id": _id}, {"$set": {"embedding": v}})
        batch_ids, batch_txts = [], []

    for d in cur:
        batch_ids.append(d["_id"])
        # ✂️ Safety truncation to avoid overly long input
        batch_txts.append(build_search_text(d)[:7000])
        if len(batch_txts) >= BATCH_SIZE:
            flush_batch()

    flush_batch()


if __name__ == "__main__":
    main()
