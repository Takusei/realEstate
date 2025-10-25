def build_search_text(doc: dict) -> str:
    flags = doc.get("flags", {}) or {}
    bits = [
        doc.get("name", ""),
        doc.get("description", ""),
        doc.get("category", ""),
        doc.get("address", ""),
        doc.get("station_line") or "",
        doc.get("station_name") or "",
        doc.get("layout_raw") or "",
        doc.get("size") or "",
        "ペット可" if flags.get("pet_ok") else "",
        "南向き" if flags.get("south_facing") else "",
        "角部屋" if flags.get("corner") else "",
        "バルコニー" if flags.get("balcony") else "",
        "タワーマンション" if flags.get("tower_mansion") else "",
    ]
    return " / ".join([b for b in bits if b])
