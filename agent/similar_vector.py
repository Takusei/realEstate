# similar_vector.py
from typing import Any, Dict, List

from bson import ObjectId
from rec_core import build_match


def similar_items_by_vector(
    PROPS, seed_id: str, filters: Dict[str, Any], index_name="rec_index"
) -> List[dict]:
    print(f"Finding items similar to ID {seed_id} with filters: {filters}")
    seed = PROPS.find_one({"_id": ObjectId(seed_id)}, {"embedding": 1})
    if not seed or not seed.get("embedding"):
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
        it["_reasons"] = ["似ている説明/設備/駅情報（ベクトル）"]
    return items[:9]
