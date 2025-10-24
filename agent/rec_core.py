import re
from typing import Any, Dict, List


def build_match(filters: dict) -> dict:
    match = {"$and": []}
    if not filters:
        return {}

    if "budget_max" in filters:
        match["$and"].append({"price_yen": {"$lte": filters["budget_max"]}})
    if "wards" in filters and filters["wards"]:
        match["$and"].append({"address": {"$regex": "|".join(filters["wards"])}})
    if "walk_max" in filters:
        match["$and"].append({"station_walk_minutes": {"$lte": filters["walk_max"]}})
    if "min_rooms" in filters and filters["min_rooms"] > 0:
        match["$and"].append({"rooms": {"$gte": filters["min_rooms"]}})
    if "min_area_sqm" in filters:
        match["$and"].append({"area_sqm": {"$gte": filters["min_area_sqm"]}})
    if filters.get("pet_ok"):
        match["$and"].append({"flags.pet_ok": True})
    if "must_have" in filters:
        for flag in filters["must_have"]:
            if flag == "balcony":
                match["$and"].append({"flags": "バルコニー"})
            elif flag == "south_facing":
                match["$and"].append({"flags": "南向き"})
            elif flag == "corner":
                match["$and"].append({"flags": "角部屋"})
            elif flag == "tower_mansion":
                match["$and"].append({"name": {"$regex": "タワー"}})

    if not match["$and"]:
        return {}
    return match


def score_item(it: Dict[str, Any], f: Dict[str, Any]) -> float:
    price = it.get("price_yen") or 10**12
    budget = f.get("budget_max") or price
    walk = it.get("station_walk_minutes") or 999
    area = it.get("area_sqm") or 0.0

    affordability = max(0, min(1, (budget - price) / max(budget, 1)))
    walkScore = 1 - min(1, (walk / f.get("walk_max", walk))) if f.get("walk_max") else 0
    areaScore = (area / f.get("min_area_sqm", area)) if f.get("min_area_sqm") else 0
    feats = f.get("must_have", [])
    featScore = (
        (sum(1 for k in feats if it.get("flags", {}).get(k)) / len(feats))
        if feats
        else 0
    )

    return 0.45 * affordability + 0.25 * walkScore + 0.20 * areaScore + 0.10 * featScore


def reasons(it: Dict[str, Any], f: Dict[str, Any]) -> List[str]:
    r = []
    if f.get("wards") and any(w in it.get("address", "") for w in f["wards"]):
        r.append(f"ご希望エリア（{'・'.join(f['wards'])}）")
    if (
        f.get("budget_max")
        and it.get("price_yen")
        and it["price_yen"] <= f["budget_max"]
    ):
        r.append(f"ご予算内（{it['price_yen']:,}円）")
    if (
        f.get("walk_max")
        and it.get("station_walk_minutes") is not None
        and it["station_walk_minutes"] <= f["walk_max"]
    ):
        r.append(f"駅徒歩{it['station_walk_minutes']}分")
    if f.get("pet_ok") and it.get("flags", {}).get("pet_ok"):
        r.append("ペット可")
    for k in f.get("must_have", []):
        if it.get("flags", {}).get(k):
            r.append(k)
    return r


# Fallback regex-based JP → filters (used only if Vertex fails/disabled)
WARD_LIST = [
    "千代田区",
    "中央区",
    "港区",
    "新宿区",
    "文京区",
    "台東区",
    "墨田区",
    "江東区",
    "品川区",
    "目黒区",
    "大田区",
    "世田谷区",
    "渋谷区",
    "中野区",
    "杉並区",
    "豊島区",
    "北区",
    "荒川区",
    "板橋区",
    "練馬区",
    "足立区",
    "葛飾区",
    "江戸川区",
]


def fallback_parse_query_to_filters(q: str) -> Dict[str, Any]:
    f: Dict[str, Any] = {}
    qn = q.replace(",", "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*億", qn)
    if m:
        f["budget_max"] = int(float(m.group(1)) * 100_000_000)
    m = re.search(r"(\d{3,5}(?:\.\d+)?)\s*万", qn)
    if m and "budget_max" not in f:
        f["budget_max"] = int(float(m.group(1)) * 10_000)
    m = re.search(r"徒歩\s*(\d{1,2})\s*分", qn)
    if m:
        f["walk_max"] = int(m.group(1))
    if "ペット" in q:
        f["pet_ok"] = True
    for n in [3, 2, 1]:
        if f"{n}LDK" in q or f"{n}ＬＤＫ" in q:
            f["min_rooms"] = max(n, f.get("min_rooms", 0))
            break
    m = re.search(r"(\d{2,3})\s*㎡|(\d{2,3})\s*m2", qn)
    if m:
        val = int([g for g in m.groups() if g][0])
        f["min_area_sqm"] = val
    f["wards"] = [w for w in WARD_LIST if w in q]
    must = []
    if "南向き" in q:
        must.append("south_facing")
    if "角部屋" in q:
        must.append("corner")
    if "バルコニー" in q:
        must.append("balcony")
    if "タワマン" in q or "タワーマンション" in q:
        must.append("tower_mansion")
    if must:
        f["must_have"] = must
    return f


# Simple TF-IDF “similar”
def combined_text(doc: Dict[str, Any]) -> str:
    bits = [
        doc.get("name", ""),
        doc.get("description", ""),
        doc.get("address", ""),
        doc.get("station_line") or "",
        doc.get("station_name") or "",
        "ペット可" if doc.get("flags", {}).get("pet_ok") else "",
        "南向き" if doc.get("flags", {}).get("south_facing") else "",
        "角部屋" if doc.get("flags", {}).get("corner") else "",
        "バルコニー" if doc.get("flags", {}).get("balcony") else "",
        "タワーマンション" if doc.get("flags", {}).get("tower_mansion") else "",
    ]
    return " / ".join([b for b in bits if b])
