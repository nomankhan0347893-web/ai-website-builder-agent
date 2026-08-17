import json
from langchain_core.messages import SystemMessage, HumanMessage
from llm import llm_light

def asset_node(state):
    """
    Finds mock assets based on the plan.
    Uses: llm_light (Mistral Large)
    """
    print("--- ASSET NODE ---")
    sys_prompt = """You are an Asset Manager for a website.
Based on the website plan, recommend exactly 3 image search keywords that would yield great stock photos for this business on Unsplash.
Also recommend exactly 3 Lucide React icon names that fit the business theme.
Return ONLY valid JSON. Do not wrap in markdown code blocks.
Structure:
{
  "image_keywords": ["modern office", "team collaboration", "laptop on desk"],
  "lucide_icons": ["Briefcase", "TrendingUp", "Users"]
}"""
    
    response = llm_light.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=json.dumps(state.get("website_plan")))])
    
    try:
        content = (response.content[0].get('text', '') if isinstance(response.content, list) else response.content).strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        assets = json.loads(content.strip())
        
        # We construct real unsplash source URLs so they render in the React code.
        real_assets = {
            "images": [f"https://source.unsplash.com/800x600/?{kw.replace(' ', ',')}" for kw in assets.get("image_keywords", ["business"])],
            "icons": assets.get("lucide_icons", ["Star", "CheckCircle", "Info"])
        }
        
        return {"assets": real_assets, "current_stage": "coding_frontend"}
    except Exception as e:
        print(f"Error parsing asset JSON: {e}")
        return {"assets": {"images": ["https://source.unsplash.com/800x600/?business"], "icons": ["Star"]}, "current_stage": "coding_frontend"}
