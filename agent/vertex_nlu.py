from typing import Dict, Any
import vertexai
import os
from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration

# Set your project + region
vertexai.init(project=os.environ.get("PROJECT_ID", 'dev-projects-476011'), location="asia-northeast1")

fn = FunctionDeclaration(
    name="extract_filters",
    description="Extract structured real-estate filters from Japanese text.",
    parameters={
        "type": "object",
        "properties": {
            "budget_max": {"type":"number","description":"Budget upper bound in yen"},
            "wards": {"type":"array","items":{"type":"string"}},
            "walk_max": {"type":"number"},
            "pet_ok": {"type":"boolean"},
            "min_rooms": {"type":"number"},
            "min_area_sqm": {"type":"number"},
            "must_have": {
                "type":"array",
                "items":{"type":"string","enum":["balcony","south_facing","corner","tower_mansion"]}
            }
        },
        "additionalProperties": False
    }
)
tool = Tool(function_declarations=[fn])

SYSTEM = (
  "あなたは日本の不動産検索条件を抽出するアシスタントです。"
  "金額正規化: 6000万=60,000,000円, 1.2億=120,000,000円。"
  "徒歩10分以内→walk_max=10。1LDK以上→min_rooms=1。"
  "品川区などの区名をwardsに。タワマン→tower_mansion。"
  "出力は必ずextract_filters関数を呼ぶこと。"
)

model = GenerativeModel("gemini-2.5-flash", system_instruction=SYSTEM)

def parse_query_to_filters_with_vertex(query: str) -> Dict[str, Any]:
    print("Using Vertex AI to parse query...", query)
    try:
        resp = model.generate_content(
            [{"role":"user","parts":[{"text": f"クエリ: {query}"}]}],
            tools=[tool],
            generation_config={"temperature":0.1},
        )
        print("Vertex response:", resp)
        if not resp.candidates:
            print("No candidates returned from Vertex AI.")
            return {}
        parts = resp.candidates[0].content.parts
        for p in parts:
            fc = getattr(p, "function_call", None)
            if fc and fc.name == "extract_filters":
                return dict(fc.args)
    except Exception as e:
        print(f"An error occurred during the Vertex AI API call: {e}")
    
    return {}
