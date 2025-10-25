# similar_vector.py
from typing import Any, Dict, List

from bson import ObjectId
from rec_core import build_match


def similar_items_by_vector(
    PROPS, seed_id: str, filters: Dict[str, Any], index_name="rec_search"
) -> List[dict]:
    seed = PROPS.find_one({"_id": ObjectId(seed_id)}, {"embedding": 1})
    if not seed or not seed.get("embedding"):
        print(f"No embedding found for seed_id: {seed_id}, using TF-IDF fallback.")
        return []  # caller can fallback to TF-IDF

    match = build_match(filters)  # from your rec_core
    pipeline = [
        {
            "$search": {
                "index": index_name,
                "knnBeta": {"path": "embedding", "vector": seed["embedding"], "k": 200},
            }
        },
        {"$match": match if match else {}},
        {"$limit": 20},
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
                "station_name": 1,
                "station_walk_minutes": 1,
                "flags": 1,
                "vector_score": {"$meta": "searchScore"},
            }
        },
    ]
    items = list(PROPS.aggregate(pipeline))
    for it in items:
        score = it.get("vector_score", 0.0)
        it["_reasons"] = [f"似ている物件（ベクトル検索 スコア: {score:.3f}）"]
    return items[:9]
