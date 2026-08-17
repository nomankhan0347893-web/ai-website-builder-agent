import json
from langchain_core.messages import SystemMessage, HumanMessage
from llm import llm_pro

def design_node(state):
    """
    Writes React/Tailwind code.
    Uses: llm_pro (Gemini Pro)
    """
    print("--- DESIGN NODE ---")
    sys_prompt = """You are an Expert Frontend Developer.
Your task is to write a COMPLETE, functional, and visually stunning React functional component named `App` for a landing page.
- Use Tailwind CSS classes for ALL styling. Make it beautiful, responsive, and modern.
- Incorporate the provided images and Lucide-react icons.
- Ensure all imports (like `import { Star } from 'lucide-react';`) are included at the top.
- The component must implement ALL the sections defined in the plan.
- Return ONLY the raw JSX code. Do not wrap in markdown ```jsx blocks. Do not include any explanations.
- CRITICAL: Keep the code concise to avoid truncation. Limit mock data arrays (like features, FAQs, testimonials) to a maximum of 2 items each.
- The code should be ready to be saved as `App.jsx` and run successfully."""

    user_prompt = f"""Plan:
{json.dumps(state.get('website_plan'), indent=2)}

Brand Colors (use these in tailwind classes like bg-[color], text-[color]):
{state.get('brand_colors')}

Assets available to use:
{json.dumps(state.get('assets'), indent=2)}

Previous Review Feedback (if any, make sure to fix these issues):
{state.get('review_feedback', 'None')}
"""
    response = llm_pro.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=user_prompt)])
    
    code = (response.content[0].get('text', '') if isinstance(response.content, list) else response.content).strip()
    if code.startswith("```jsx"):
        code = code[6:]
    elif code.startswith("```javascript"):
        code = code[14:]
    elif code.startswith("```"):
        code = code[3:]
        
    if code.endswith("```"):
        code = code[:-3]
        
    return {"frontend_code": code.strip(), "current_stage": "coding_backend"}
