import re
from typing import Any, Dict, List


def build_match(filters: dict) -> dict:
    match = {"$and": []}
    if not filters:
        return {}

    # price
    if "budget_max" in filters:
        match["$and"].append({"price_yen": {"$lte": filters["budget_max"]}})

    # wards
    if "wards" in filters and filters["wards"]:
        ward_pat = "|".join(re.escape(w) for w in filters["wards"])
        match["$and"].append({"address": {"$regex": ward_pat, "$options": "i"}})

    # station
    if "station_name" in filters and filters["station_name"]:
        station_pat = re.escape(filters["station_name"])
        match["$and"].append({"station_name": {"$regex": station_pat, "$options": "i"}})

    # walk
    if "walk_max" in filters:
        match["$and"].append({"station_walk_minutes": {"$lte": filters["walk_max"]}})

    # rooms
    if "min_rooms" in filters and filters["min_rooms"] > 0:
        match["$and"].append({"rooms": {"$gte": filters["min_rooms"]}})

    # area
    if "min_area_sqm" in filters:
        match["$and"].append({"area_sqm": {"$gte": filters["min_area_sqm"]}})

    # flags
    if filters.get("pet_ok"):
        match["$and"].append({"flags.pet_ok": True})
    if filters.get("bal_ok"):
        match["$and"].append({"flags.balcony": True})
    if filters.get("south_ok"):
        match["$and"].append({"flags.south_facing": True})
    if filters.get("corner_ok"):
        match["$and"].append({"flags.corner": True})
    if filters.get("tower_ok"):
        match["$and"].append({"flags.tower_mansion": True})

    return match if match["$and"] else {}


def score_item(it: Dict[str, Any], f: Dict[str, Any]) -> float:
    price = it.get("price_yen") or 10**12
    budget = f.get("budget_max") or price
    walk = it.get("station_walk_minutes") or 999
    area = it.get("area_sqm") or 0.0

    affordability = max(0, min(1, (budget - price) / max(budget, 1)))
    walkScore = 1 - min(1, (walk / f.get("walk_max", walk))) if f.get("walk_max") else 0
    areaScore = (area / f.get("min_area_sqm", area)) if f.get("min_area_sqm") else 0

    # feature score based on individual flags
    flag_keys = [
        ("bal_ok", "balcony"),
        ("south_ok", "south_facing"),
        ("corner_ok", "corner"),
        ("tower_ok", "tower_mansion"),
        ("pet_ok", "pet_ok"),
    ]
    required = [k for k, _ in flag_keys if f.get(k)]
    matched = sum(
        1 for key, flag in flag_keys if f.get(key) and it.get("flags", {}).get(flag)
    )
    featScore = (matched / len(required)) if required else 0

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
    if f.get("bal_ok") and it.get("flags", {}).get("balcony"):
        r.append("バルコニー")
    if f.get("south_ok") and it.get("flags", {}).get("south_facing"):
        r.append("南向き")
    if f.get("corner_ok") and it.get("flags", {}).get("corner"):
        r.append("角部屋")
    if f.get("tower_ok") and it.get("flags", {}).get("tower_mansion"):
        r.append("タワマン")
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
    # normalize input a bit
    qn = q.replace(",", "").replace("，", "").strip()

    # ---- budget: “1.2億”, “6000万”, “6,000万円”など ----
    m = re.search(r"(\d+(?:\.\d+)?)\s*億", qn)
    if m:
        f["budget_max"] = int(float(m.group(1)) * 100_000_000)
    m = re.search(r"(\d{3,6}(?:\.\d+)?)\s*万", qn)  # 万 or 万円
    if m and "budget_max" not in f:
        f["budget_max"] = int(float(m.group(1)) * 10_000)

    # ---- walk: “徒歩10分”, “徒歩10分以内” ----
    m = re.search(r"徒歩\s*(\d{1,2})\s*分", qn)
    if m:
        f["walk_max"] = int(m.group(1))

    # ---- pets ----
    if "ペット" in q:
        f["pet_ok"] = True

    # ---- rooms: 1LDK/２LDK/３ＬＤＫ etc. (full/half width) ----
    # check 3, then 2, then 1 to capture "以上"ニュアンス
    for n in [3, 2, 1]:
        if re.search(rf"[{n}１２３]LDK|[{n}１２３]ＬＤＫ", qn):
            f["min_rooms"] = max(n, f.get("min_rooms", 0))
            break

    # ---- area: “45㎡”, “45m2” ----
    m = re.search(r"(?:([0-9]{2,3})\s*㎡|([0-9]{2,3})\s*m2)", qn, re.IGNORECASE)
    if m:
        val = int(next(g for g in m.groups() if g))
        f["min_area_sqm"] = val

    # ---- wards ----
    f["wards"] = [w for w in WARD_LIST if w in q]

    # ---- feature flags (no more must_have) ----
    if "南向き" in q:
        f["south_ok"] = True
    if "角部屋" in q:
        f["corner_ok"] = True
    if "バルコニー" in q:
        f["bal_ok"] = True
    if ("タワマン" in q) or ("タワーマンション" in q):
        f["tower_ok"] = True

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
