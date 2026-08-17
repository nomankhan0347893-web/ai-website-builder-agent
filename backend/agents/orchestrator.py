import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from llm import llm_pro

def orchestrator_node(state):
    """
    Plans the website sections or reviews the generated code.
    Uses: llm_pro (Gemini Pro)
    """
    stage = state.get("current_stage", "planning")
    print(f"--- ORCHESTRATOR NODE: {stage.upper()} ---")
    
    if stage == "planning":
        sys_prompt = """You are an expert Website Architect. Your job is to plan the sections for a landing page based on the business description.
Think deeply about what sections would convert visitors into customers for this specific business.
Return ONLY a valid JSON object. Do NOT wrap it in markdown code blocks.
The JSON must follow this exact structure:
{
  "sections": [
    {
      "id": "hero",
      "name": "Hero Section",
      "description": "A compelling headline, a subheadline, and a call-to-action button.",
      "needs_image": true,
      "needs_icon": false
    },
    {
      "id": "services",
      "name": "Services",
      "description": "List of 3 main services offered.",
      "needs_image": false,
      "needs_icon": true
    }
  ]
}"""
        user_prompt = f"Business Description: {state.get('business_description')}\nTone: {state.get('tone')}"
        
        response = llm_pro.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=user_prompt)])
        
        try:
            content = (response.content[0].get('text', '') if isinstance(response.content, list) else response.content).strip()
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
            if match:
                content = match.group(1)
            plan = json.loads(content.strip())
            return {"website_plan": plan, "current_stage": "generating_assets"}
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return {"website_plan": {"error": "Failed to generate plan"}, "current_stage": "generating_assets"}
            
    elif stage == "reviewing":
        sys_prompt = """You are a strict QA Tester. Review the generated frontend React code and backend Express code against the original plan.
Ensure the frontend uses Tailwind CSS and includes all sections from the plan.
If the code is missing sections, has syntax errors, or ignores the plan, return a JSON with status "failed" and feedback.
If it looks complete and correct, return status "passed".
Return ONLY valid JSON:
{
    "status": "passed",
    "feedback": "Your detailed feedback on what needs to be fixed if failed. Leave empty if passed."
}"""
        user_prompt = f"Plan: {json.dumps(state.get('website_plan'))}\n\nFrontend Code:\n{state.get('frontend_code')}\n\nBackend Code:\n{state.get('backend_code')}"
        
        response = llm_pro.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=user_prompt)])
        try:
            content = (response.content[0].get('text', '') if isinstance(response.content, list) else response.content).strip()
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
            if match:
                content = match.group(1)
            review = json.loads(content.strip())
            
            if review.get("status") == "passed":
                return {"review_status": "passed", "current_stage": "execution", "review_feedback": ""}
            else:
                return {"review_status": "failed", "current_stage": "coding_frontend", "review_feedback": review.get("feedback")}
        except Exception as e:
            print(f"Failed to parse review JSON: {e}. Defaulting to passed.")
            return {"review_status": "passed", "current_stage": "execution", "review_feedback": ""}

    return {"current_stage": "execution"}
