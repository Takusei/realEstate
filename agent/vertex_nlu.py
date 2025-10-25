import os
from typing import Any, Dict

from google import genai
from google.genai import types

# ---- Client (Vertex mode; uses project/location like your old code) ----
client = genai.Client(
    vertexai=True,
    project=os.environ.get("PROJECT_ID", "dev-projects-476011"),
    location="asia-northeast1",
)

# ---- Function declaration & tool (schema equivalent to your original) ----
extract_filters_fn = types.FunctionDeclaration(
    name="extract_filters",
    description="Extract structured real-estate filters from Japanese text.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "budget_max": types.Schema(
                type="NUMBER",
                description="Budget upper bound in yen",
            ),
            "wards": types.Schema(
                type="ARRAY",
                items=types.Schema(type="STRING"),
            ),
            "walk_max": types.Schema(type="NUMBER"),
            "station_name": types.Schema(type="STRING"),
            "pet_ok": types.Schema(type="BOOLEAN"),
            "min_rooms": types.Schema(type="NUMBER"),
            "min_area_sqm": types.Schema(type="NUMBER"),
            "balcony": types.Schema(type="BOOLEAN"),
            "south_facing": types.Schema(type="BOOLEAN"),
            "corner": types.Schema(type="BOOLEAN"),
            "tower_mansion": types.Schema(type="BOOLEAN"),
        },
        additional_properties=False,
    ),
)

tool = types.Tool(function_declarations=[extract_filters_fn])

SYSTEM = (
    "あなたは日本の不動産検索条件を抽出するアシスタントです。"
    "金額正規化: 6000万=60,000,000円, 1.2億=120,000,000円。"
    "徒歩10分以内→walk_max=10。1LDK以上→min_rooms=1。"
    "品川区などの区名をwardsに。タワマン→tower_mansion。"
    "電車の駅名があればstation_nameに入れてください。"
    "もし電車の駅名があれば、その駅名を検索し、必ず対応する区名をwardsにも追加してください。"
    "出力は必ずextract_filters関数を呼ぶこと。"
)


def parse_query_to_filters_with_vertex(query: str) -> Dict[str, Any]:
    """
    Generates a function call to `extract_filters` and returns its arguments as a dict.
    Mirrors the behavior of your previous Vertex SDK code.
    """
    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"クエリ: {query}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM,
                tools=[tool],  # manual declaration; model returns a function call
                temperature=0.1,
            ),
        )
        # When tools are declared manually, the SDK exposes function calls here:
        # - resp.function_calls: flat list of function-call parts (convenient)
        # - resp.candidates[0].content.parts: raw parts (if you prefer to scan)
        if not getattr(resp, "function_calls", None):
            # No function call produced
            return {}

        # Find the first call to extract_filters and return its args
        for fc in resp.function_calls:
            if fc.name == "extract_filters":
                # fc.args is a dict-like object already
                return dict(fc.args)

        return {}
    except Exception as e:
        print(f"An error occurred during the Google GenAI API call: {e}")
        return {}
