from langchain_core.messages import SystemMessage, HumanMessage
from llm import llm_light

def backend_node(state):
    """
    Writes Node.js contact form server.
    Uses: llm_light (Mistral Large)
    """
    print("--- BACKEND NODE ---")
    sys_prompt = """You are a Backend Developer.
Your task is to write a COMPLETE, functional Node.js Express server (`server.js`).
It must contain:
1. Express initialization with CORS and JSON body parsing.
2. A single POST route at `/api/contact` that accepts { name, email, message }.
3. The route should simply log the message to the console and return a success JSON response.
4. The server should listen on port 3001.

Return ONLY the raw JavaScript code. Do not wrap in markdown ```javascript blocks. Do not include any explanations.
The code should be ready to be saved as `server.js` and run successfully."""
    
    response = llm_light.invoke([SystemMessage(content=sys_prompt), HumanMessage(content="Write the server code.")])
    
    code = (response.content[0].get('text', '') if isinstance(response.content, list) else response.content).strip()
    if code.startswith("```javascript"):
        code = code[14:]
    elif code.startswith("```js"):
        code = code[5:]
    elif code.startswith("```"):
        code = code[3:]
        
    if code.endswith("```"):
        code = code[:-3]
        
    return {"backend_code": code.strip(), "current_stage": "reviewing"}
