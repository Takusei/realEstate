# rag_generate.py
import os

import vertexai
from vertexai.generative_models import Content, GenerativeModel, Part

vertexai.init(
    project=os.getenv("PROJECT_ID", "dev-projects-476011"),
    location="asia-northeast1",
)

SYSTEM = (
    "あなたは不動産アドバイザーです。ユーザー条件と候補物件の一覧を読み、"
    "最大3件を推薦し、理由を日本語で簡潔に述べます。"
    "価格・駅徒歩・面積・設備（ペット可/南向き/角部屋/バルコニー/タワーマンション）に基づき、"
    "条件に合わない場合は『合致候補なし』と返してください。"
    "出力は次のJSONのみ:\n"
    '{ "recommendations": [ {"name":"...","url":"...","reason":"..."} ] }'
)

MODEL = GenerativeModel("gemini-2.5-flash", system_instruction=SYSTEM)


def format_context(items: list[dict]) -> str:
    lines = []
    for it in items[:12]:
        lines.append(
            f"- {it.get('name', '(不明)')} | {it.get('address', '')} | "
            f"{it.get('price_yen', '-')}円 | 徒歩{it.get('station_walk_minutes', '-')}分 | "
            f"{it.get('area_sqm', '-')}㎡ | {it.get('layout_raw') or (('ワンルーム') if (it.get('rooms') == 0) else f'{it.get("rooms", "-")}R')} | "
            f"設備: ペット可={bool(it.get('flags', {}).get('pet_ok'))}, 南向き={bool(it.get('flags', {}).get('south_facing'))}, "
            f"角部屋={bool(it.get('flags', {}).get('corner'))}, バルコニー={bool(it.get('flags', {}).get('balcony'))}, "
            f"タワマン={bool(it.get('flags', {}).get('tower_mansion'))} | URL={it.get('url', '#')}"
        )
    return "\n".join(lines)


def generate_summary(user_query: str, items: list[dict]) -> str:
    ctx = format_context(items)
    user = Content(
        role="user",
        parts=[
            Part.from_text(
                f"ユーザーのクエリ: {user_query}\n候補物件:\n{ctx}\n"
                "上記だけを根拠として、JSONで出力してください。余計な文章は禁止。"
            )
        ],
    )
    resp = MODEL.generate_content([user], generation_config={"temperature": 0.1})
    # return raw text (should be JSON)
    return resp.candidates[0].content.parts[0].text
