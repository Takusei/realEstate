import os, uuid, time
import streamlit as st
from bson import ObjectId
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from db import get_collections
from rec_core import build_match, score_item, reasons, fallback_parse_query_to_filters, combined_text
from vertex_nlu import parse_query_to_filters_with_vertex

from rec_core import fallback_parse_query_to_filters
from vertex_guard import cached_ttl_parse
import streamlit as st, time
import os, streamlit as st

APP_PIN = os.getenv("APP_PIN")  # set in Cloud Run env

if APP_PIN:
    if "authed" not in st.session_state:
        st.session_state.authed = False
    if not st.session_state.authed:
        st.title("🔒 Private Demo")
        pin = st.text_input("Enter PIN", type="password")
        if st.button("Unlock") and pin == APP_PIN:
            st.session_state.authed = True
            st.rerun()
        st.stop()

MAX_CALLS_PER_SESSION = 10

if "vertex_calls" not in st.session_state:
    st.session_state["vertex_calls"] = 0

def parse_with_guard(q: str):
    if not q.strip():
        return {}
    try:
        if st.session_state["vertex_calls"] >= MAX_CALLS_PER_SESSION:
            st.info("Vertex上限に到達: フォールバック解析を使用します。")
            return fallback_parse_query_to_filters(q)
        out = cached_ttl_parse(q, ttl_sec=600)
        st.session_state["vertex_calls"] += 1
        return out
    except Exception as e:
        st.warning(f"Vertex利用不可: フォールバック解析 ({e})")
        return fallback_parse_query_to_filters(q)


st.set_page_config(page_title="不動産レコメンド", layout="wide")

PROPS, EVENTS = get_collections()
if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())[:8]

st.title("🏠 不動産レコメンド（デモ）")
st.caption("例：「品川区で6000万円以下、駅徒歩10分以内、ペット可、1LDK以上」")

with st.sidebar:
    st.header("🔎 絞り込み（任意）")
    wards = st.multiselect("エリア（区）", ["品川区","目黒区","港区","渋谷区","世田谷区","大田区","中央区","千代田区"])
    budget_max_man = st.number_input("予算上限（万円）", min_value=0, step=100, value=0)
    walk_max = st.slider("徒歩分数（上限）", 1, 20, 10)
    min_rooms = st.selectbox("最小部屋数", options=[0,1,2,3], index=1, format_func=lambda x: "ワンルーム可" if x==0 else f"{x}以上")
    min_area = st.number_input("最小専有面積（㎡）", min_value=0, step=5, value=0)
    pet_ok = st.checkbox("ペット可", value=False)
    must_bal = st.checkbox("バルコニー")
    must_south = st.checkbox("南向き")
    must_corner = st.checkbox("角部屋")
    must_tower = st.checkbox("タワマン")
    run_btn = st.button("検索")

q = st.text_input("クエリ", placeholder="品川区で6000万円以下、駅徒歩10分以内、ペット可、1LDK以上")

def collect_filters():
    f = {}
    # ✨ Rate-limited Vertex call here
    if q.strip():
        f.update(parse_with_guard(q))

    print("Parsed filters from query:", f)
    # sidebar overrides
    if wards: f["wards"] = wards
    if budget_max_man and budget_max_man > 0: f["budget_max"] = budget_max_man * 10_000
    if walk_max: f["walk_max"] = walk_max
    f["min_rooms"] = min_rooms
    if min_area and min_area > 0: f["min_area_sqm"] = min_area
    if pet_ok: f["pet_ok"] = True
    must = []
    if must_bal: must.append("balcony")
    if must_south: must.append("south_facing")
    if must_corner: must.append("corner")
    if must_tower: must.append("tower_mansion")
    if must: f["must_have"] = must
    return f

def log_event(item_id: str, action: str):
    EVENTS.insert_one({"user_id": st.session_state["user_id"], "item_id": str(item_id), "action": action, "ts": time.time()})

def recommend(filters):
    match = build_match(filters)
    cursor = PROPS.find(match, {
        "name":1,"address":1,"image":1,"url":1,
        "price_yen":1,"area_sqm":1,"rooms":1,"ldk":1,"layout_raw":1,"size":1,
        "station_name":1,"station_walk_minutes":1,"flags":1,"description":1
    }).limit(250)

    seen_names = set()
    unique_items = []
    for item in list(cursor):
        name = item.get("name")
        if name not in seen_names:
            unique_items.append(item)
            if name:
                seen_names.add(name)
    
    items = unique_items
    for it in items:
        it["_score"] = score_item(it, filters)
        it["_reasons"] = reasons(it, filters)
    items.sort(key=lambda x: x["_score"], reverse=True)
    return items[:12]

def similar_items(seed_id: str, filters):
    seed = PROPS.find_one({"_id": ObjectId(seed_id)}, {"name":1,"description":1,"address":1,"flags":1,"station_line":1,"station_name":1})
    if not seed: return []
    match = build_match(filters)
    cands = list(PROPS.find(match, {
        "_id":1,"name":1,"image":1,"url":1,"description":1,"address":1,"flags":1,
        "price_yen":1,"area_sqm":1,"rooms":1,"layout_raw":1,"size":1,
        "station_name":1,"station_walk_minutes":1,"station_line":1
    }).limit(400))
    texts = [combined_text(seed)] + [combined_text(c) for c in cands]
    tf = TfidfVectorizer(min_df=2).fit_transform(texts)
    sims = cosine_similarity(tf[0:1], tf[1:]).ravel()
    paired = list(zip(cands, sims))
    paired.sort(key=lambda x: x[1], reverse=True)
    top = [p[0] for p in paired[:9]]
    for it in top:
        it["_reasons"] = ["似ている説明/設備/駅情報（類似検索）"]
    return top

def render_cards(items, key_prefix=""):
    cols = st.columns(3)
    for idx, it in enumerate(items):
        with cols[idx % 3]:
            image_url = it.get("image","")
            if image_url:
              st.image(image_url, width=500)
            else:
              st.text("No Image Available")
            st.markdown(f"**{it.get('name') or '(物件名なし)'}**")
            st.caption(f"{it.get('address','')}｜{it.get('station_name','')}駅 徒歩{it.get('station_walk_minutes','-')}分")
            layout = it.get("layout_raw") or ("ワンルーム" if (it.get("rooms")==0) else f"{it.get('rooms','-')}R")
            size   = it.get("size") or (f"{it.get('area_sqm','-')}㎡")
            
            price = it.get('price_yen')
            price_str = f"{price:,}" if isinstance(price, (int, float)) else "-"
            
            st.markdown(f"価格: **{price_str}円**｜{size}｜間取り: {layout}")
            chips = " / ".join(it.get("_reasons", []))
            if chips: st.info(chips)

            button_key = f"{key_prefix}-sim-{it['_id']}"
            if st.button("似た物件", key=button_key):
                st.session_state["similar_id"] = str(it["_id"])
                st.session_state["show_similar"] = True

            st.link_button("詳細を見る", it.get("url","#"))

if run_btn or q:
    st.subheader("おすすめ物件")
    with st.spinner("物件を検索中..."):
        filters = collect_filters()
        recommended_items = recommend(filters)
        render_cards(recommended_items, key_prefix="rec")

if st.session_state.get("show_similar") and (sid := st.session_state.get("similar_id")):
    st.subheader("似た物件")
    with st.spinner("似た物件を探しています..."):
        # We need filters for the similar items search as well
        filters = collect_filters()
        similar_items_list = similar_items(sid, filters)
        render_cards(similar_items_list, key_prefix="sim")
