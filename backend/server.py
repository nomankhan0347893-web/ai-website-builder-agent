from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from main import app as agent_app

app = FastAPI()

# Allow the React frontend to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import uuid
import os
import dotenv
import urllib.request
import json

dotenv.load_dotenv(override=True)

active_thread_id = "1"

def get_config():
    return {"configurable": {"thread_id": active_thread_id}}

class StartRequest(BaseModel):
    business_description: str
    tone: str
    brand_colors: Optional[List[str]] = None

@app.post("/api/start")
async def start_generation(request: StartRequest, background_tasks: BackgroundTasks):
    global active_thread_id
    active_thread_id = str(uuid.uuid4())
    config = get_config()
    
    initial_state = {
        "business_description": request.business_description,
        "tone": request.tone,
        "brand_colors": request.brand_colors,
        "human_approval": False
    }
    
    # We run the graph in the background so the HTTP request returns immediately
    def run_graph():
        print(f"Starting LangGraph execution for thread {active_thread_id}...")
        for event in agent_app.stream(initial_state, config):
            try:
                print(event)
            except UnicodeEncodeError:
                print(str(event).encode('ascii', 'replace').decode('ascii'))
            
    background_tasks.add_task(run_graph)
    return {"status": "Generation started in the background."}

@app.get("/api/settings")
async def get_settings():
    """
    Returns the current environment variables configuration.
    """
    dotenv_path = os.path.abspath(".env")
    env_vars = dotenv.dotenv_values(dotenv_path)
    return {
        "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", env_vars.get("GOOGLE_API_KEY", "")),
        "NETLIFY_AUTH_TOKEN": os.environ.get("NETLIFY_AUTH_TOKEN", env_vars.get("NETLIFY_AUTH_TOKEN", "")),
        "MISTRAL_API_KEY": os.environ.get("MISTRAL_API_KEY", env_vars.get("MISTRAL_API_KEY", "")),
        "VERCEL_TOKEN": os.environ.get("VERCEL_TOKEN", env_vars.get("VERCEL_TOKEN", ""))
    }

class SettingsUpdateRequest(BaseModel):
    GOOGLE_API_KEY: Optional[str] = None
    NETLIFY_AUTH_TOKEN: Optional[str] = None
    MISTRAL_API_KEY: Optional[str] = None
    VERCEL_TOKEN: Optional[str] = None

@app.post("/api/settings")
async def update_settings(request: SettingsUpdateRequest):
    """
    Updates the .env file and live os.environ with user-provided API keys.
    """
    dotenv_path = os.path.abspath(".env")
    
    updates = {}
    if request.GOOGLE_API_KEY is not None:
        updates["GOOGLE_API_KEY"] = request.GOOGLE_API_KEY
    if request.NETLIFY_AUTH_TOKEN is not None:
        updates["NETLIFY_AUTH_TOKEN"] = request.NETLIFY_AUTH_TOKEN
    if request.MISTRAL_API_KEY is not None:
        updates["MISTRAL_API_KEY"] = request.MISTRAL_API_KEY
    if request.VERCEL_TOKEN is not None:
        updates["VERCEL_TOKEN"] = request.VERCEL_TOKEN

    for key, val in updates.items():
        if val:
            os.environ[key] = val
            dotenv.set_key(dotenv_path, key, val)

    return {"status": "success", "message": "Settings updated successfully!"}

@app.get("/api/status")
async def get_status():
    """
    The frontend will poll this endpoint to see what stage the AI is at,
    and to check if the AI has paused to ask for permission.
    """
    config = get_config()
    state = agent_app.get_state(config)
    
    if not state or not hasattr(state, 'values'):
        return {"status": "idle", "is_paused": False, "state": {}}

    is_paused = len(state.next) > 0 and "run_commands" in state.next
    current_stage = state.values.get("current_stage", "")
    
    if current_stage == "completed":
        status_str = "completed"
    elif is_paused:
        status_str = "paused_awaiting_approval"
    elif current_stage == "denied":
        status_str = "denied"
    else:
        status_str = "running"
    
    return {
        "status": status_str,
        "is_paused": is_paused,
        "next_nodes": state.next,
        "state": state.values
    }

class ApproveRequest(BaseModel):
    approved: bool

@app.post("/api/approve")
async def approve_execution(request: ApproveRequest, background_tasks: BackgroundTasks):
    """
    The frontend hits this when the user clicks 'Approve' or 'Deny' on the terminal commands.
    """
    config = get_config()
    def resume_graph():
        print(f"Resuming graph for thread {active_thread_id}. Human Approval: {request.approved}")
        # Inject the human's decision into the state
        agent_app.update_state(config, {"human_approval": request.approved})
        
        # Resume the graph from where it paused by passing None
        for event in agent_app.stream(None, config):
            try:
                print(event)
            except UnicodeEncodeError:
                print(str(event).encode('ascii', 'replace').decode('ascii'))
            
    background_tasks.add_task(resume_graph)
    return {"status": "Graph resumed."}

class FeedbackRequest(BaseModel):
    feedback: str

@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest, background_tasks: BackgroundTasks):
    """
    Allows the user to describe changes in plain language.
    The orchestrator and design agent immediately update the code and live preview.
    """
    config = get_config()
    current_state = agent_app.get_state(config).values if agent_app.get_state(config) else {}
    
    def run_feedback_loop():
        print(f"Applying user feedback on thread {active_thread_id}: {request.feedback}")
        from agents import design_node, backend_node, orchestrator_node, execution_node, run_commands_node
        
        updated_state = dict(current_state)
        updated_state["review_feedback"] = f"User Requested Changes: {request.feedback}"
        updated_state["current_stage"] = "coding_frontend"
        agent_app.update_state(config, updated_state)
        
        # Step 1: Design Node redesigns the website with user feedback
        print("--- RE-DESIGNING WITH USER FEEDBACK ---")
        design_output = design_node(updated_state)
        updated_state.update(design_output)
        agent_app.update_state(config, updated_state)
        
        # Step 2: Backend Node
        print("--- RE-CHECKING BACKEND ---")
        updated_state["current_stage"] = "coding_backend"
        backend_output = backend_node(updated_state)
        updated_state.update(backend_output)
        agent_app.update_state(config, updated_state)
        
        # Step 3: Review Node
        print("--- REVIEWING REVISED CODE ---")
        updated_state["current_stage"] = "reviewing"
        review_output = orchestrator_node(updated_state)
        updated_state.update(review_output)
        agent_app.update_state(config, updated_state)
        
        # Step 4: Execution Node
        print("--- PREPARING EXECUTION ---")
        updated_state["current_stage"] = "execution"
        exec_output = execution_node(updated_state)
        updated_state.update(exec_output)
        agent_app.update_state(config, updated_state)
        
        # Step 5: Automatically apply and commit the refinement
        print("--- APPLYING REVISED FILES & GIT COMMIT ---")
        updated_state["human_approval"] = True
        run_output = run_commands_node(updated_state)
        updated_state.update(run_output)
        agent_app.update_state(config, updated_state)
        print("Refinement successfully completed and live preview updated!")

    background_tasks.add_task(run_feedback_loop)
    return {"status": "Refinement started in the background."}

class DeployPrepareRequest(BaseModel):
    service: str = "netlify_drop" # netlify_drop, vercel, netlify, localtunnel

class DeployExecuteRequest(BaseModel):
    service: str = "netlify_drop"
    approved: bool

@app.post("/api/deploy/prepare")
async def prepare_deploy(request: DeployPrepareRequest):
    """
    Asks the Execution Agent to prepare deployment commands for user approval.
    """
    config = get_config()
    state = agent_app.get_state(config)
    
    desc = state.values.get("business_description", "my_site") if state and hasattr(state, 'values') else "my_site"
    raw_name = desc[:15].strip().replace(" ", "_").lower()
    business_name = re.sub(r'[^a-z0-9_]', '', raw_name) or "website"
    
    frontend_dir = os.path.abspath(f"../generated-sites/{business_name}/frontend")
    
    if request.service == "netlify_drop":
        command = f"explorer.exe \"{frontend_dir}\""
        live_link = "https://app.netlify.com/drop"
        service_name = "Netlify Drop (1-Click Drag & Drop, No Account Required)"
        safety_note = f"Opens Netlify Drop and your project folder at '{frontend_dir}'. Drag the folder into Netlify for an instant, permanent .netlify.app live website!"
    elif request.service == "vercel":
        command = f"cd \"{frontend_dir}\" && npx -y vercel --prod --yes"
        live_link = f"https://{business_name}.vercel.app"
        service_name = "Vercel CLI"
        safety_note = "Deploys directly to your Vercel account. (Requires 'npx vercel login' in terminal)."
    elif request.service == "netlify":
        command = f"cd \"{frontend_dir}\" && npx -y netlify-cli deploy --dir=. --prod"
        live_link = f"https://{business_name}.netlify.app"
        service_name = "Netlify CLI"
        safety_note = "Deploys directly to Netlify using Netlify CLI."
    else:
        command = f"cd \"{frontend_dir}\" && npx -y surge . --domain {business_name}-live.surge.sh"
        live_link = f"https://{business_name}-live.surge.sh"
        service_name = "Surge.sh"
        safety_note = f"Deploys your standalone website to Surge cloud hosting."
        
    return {
        "service": request.service,
        "service_name": service_name,
        "command": command,
        "business_name": business_name,
        "frontend_dir": frontend_dir,
        "live_link": live_link,
        "safety_note": safety_note
    }

import zipfile
import io

def deploy_to_netlify_direct(frontend_dir: str, site_name: str, token: str = None) -> dict:
    """
    Directly packages and deploys the site to Netlify cloud via REST API.
    """
    token = token or os.environ.get("NETLIFY_AUTH_TOKEN")
    
    # 1. Create _headers file to ensure Netlify serves index.html as text/html
    headers_file = os.path.join(frontend_dir, "_headers")
    try:
        with open(headers_file, "w", encoding="utf-8") as f:
            f.write("/*\n  Content-Type: text/html; charset=UTF-8\n")
    except Exception:
        pass

    # 2. Create in-memory zip of frontend directory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(frontend_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, frontend_dir)
                z.write(abs_path, rel_path)
        z.writestr("_headers", "/*\n  Content-Type: text/html; charset=UTF-8\n")
    zip_bytes = buf.getvalue()
    
    if token:
        try:
            # 1. Fetch user's account slug
            acc_req = urllib.request.Request(
                "https://api.netlify.com/api/v1/accounts",
                headers={"Authorization": f"Bearer {token}"}
            )
            slug = "kashifkhan09001"
            try:
                with urllib.request.urlopen(acc_req, timeout=10) as a_res:
                    accs = json.loads(a_res.read().decode("utf-8"))
                    if accs and len(accs) > 0:
                        slug = accs[0].get("slug", slug)
            except Exception:
                pass

            # 2. Deploy directly to the user's account
            req = urllib.request.Request(
                f"https://api.netlify.com/api/v1/{slug}/sites",
                data=zip_bytes,
                headers={
                    "Content-Type": "application/zip",
                    "Authorization": f"Bearer {token}"
                }
            )
            with urllib.request.urlopen(req, timeout=30) as res:
                data = json.loads(res.read().decode("utf-8"))
                subdomain = data.get("subdomain") or "site"
                live_url = f"https://{subdomain}.netlify.app"
                return {"success": True, "url": live_url, "provider": "Netlify Cloud", "subdomain": subdomain}
        except Exception as e:
            print(f"Netlify API token deploy failed: {e}")

    return {"success": False, "provider": "Netlify"}

@app.post("/api/deploy/execute")
async def execute_deploy(request: DeployExecuteRequest):
    """
    Executes the deployment directly via Execution Agent and returns the live public link.
    """
    if not request.approved:
        return {"status": "denied", "message": "Deployment canceled by user."}
        
    config = get_config()
    state = agent_app.get_state(config)
    desc = state.values.get("business_description", "my_site") if state and hasattr(state, 'values') else "my_site"
    raw_name = desc[:15].strip().replace(" ", "_").lower()
    business_name = re.sub(r'[^a-z0-9_]', '', raw_name) or "website"
    frontend_dir = os.path.abspath(f"../generated-sites/{business_name}/frontend")
    os.makedirs(frontend_dir, exist_ok=True)
    
    # Ensure index.html exists in frontend directory
    index_path = os.path.join(frontend_dir, "index.html")
    app_jsx_path = os.path.join(frontend_dir, "src", "App.jsx")
    code = ""
    if os.path.exists(app_jsx_path):
        try:
            with open(app_jsx_path, "r", encoding="utf-8") as f:
                code = f.read()
        except Exception:
            pass
    elif state and hasattr(state, 'values'):
        code = state.values.get("frontend_code", "")
        
    if code:
        try:
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(build_preview_html(code))
        except Exception as e:
            print(f"Error writing deploy index.html: {e}")

    # Check for direct Netlify API deployment
    netlify_res = deploy_to_netlify_direct(frontend_dir, business_name)
    if netlify_res.get("success"):
        return {
            "status": "success",
            "deployed_url": netlify_res.get("url"),
            "frontend_dir": frontend_dir,
            "service_name": "Netlify Cloud",
            "message": f"Website was directly published online by the Execution Agent!"
        }

    import webbrowser
    if request.service == "netlify_drop":
        try:
            subprocess.Popen(f'explorer "{frontend_dir}"')
            webbrowser.open("https://app.netlify.com/drop")
        except Exception:
            pass
        deployed_url = "https://app.netlify.com/drop"
        message = f"Opened project folder! Drag '{frontend_dir}' into Netlify Drop in your browser for instant free hosting."
    elif request.service == "vercel":
        deployed_url = f"https://vercel.com/new"
        try:
            webbrowser.open("https://vercel.com/new")
        except Exception:
            pass
        message = "Opened Vercel Import! You can connect your Git repository or CLI to deploy to Vercel."
    else:
        deployed_url = f"https://{business_name}-live.surge.sh"
        message = f"Website packaged for deployment to {request.service.capitalize()}!"

    return {
        "status": "success",
        "deployed_url": deployed_url,
        "frontend_dir": frontend_dir,
        "service_name": request.service.capitalize(),
        "message": message
    }

from fastapi.responses import HTMLResponse
import re
import glob
import os

def build_preview_html(app_code: str):
    def replace_unsplash(match):
        width_height = match.group(1)
        width, height = width_height.split('x')
        return f"https://picsum.photos/seed/{match.group(2)[:10]}/{width}/{height}"
    
    clean_code = re.sub(r"https://source\.unsplash\.com/(\d+x\d+)/\?([^\"']+)", replace_unsplash, app_code)
    clean_code = re.sub(r'export\s+default\s+function\s+App', 'function App', clean_code)
    clean_code = re.sub(r'export\s+function\s+App', 'function App', clean_code)
    clean_code = re.sub(r'export\s+default\s+App\s*;?', '', clean_code)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Live Preview</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script type="importmap">
    {{
      "imports": {{
        "react": "https://esm.sh/react@18.2.0",
        "react-dom/client": "https://esm.sh/react-dom@18.2.0/client",
        "lucide-react": "https://esm.sh/lucide-react@0.263.1?deps=react@18.2.0"
      }}
    }}
  </script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
</head>
<body class="bg-[#0F172A] text-slate-100 min-h-screen">
  <div id="root"></div>
  <script type="text/babel" data-type="module">
    import {{ createRoot }} from 'react-dom/client';
    
{clean_code}

    createRoot(document.getElementById('root')).render(<App />);
  </script>
</body>
</html>"""

@app.get("/api/preview", response_class=HTMLResponse)
async def get_preview():
    """
    Renders the live, interactive preview of the currently active website project.
    """
    config = get_config()
    state = agent_app.get_state(config)
    
    code = ""
    if state and hasattr(state, 'values') and state.values:
        code = state.values.get("frontend_code", "")
        stage = state.values.get("current_stage", "")
        if not code and stage in ["planning", "generating_assets", "coding_frontend"]:
            return HTMLResponse("""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#0F172A] text-slate-200 min-h-screen flex items-center justify-center font-sans p-6">
  <div class="text-center space-y-4 max-w-md">
    <div class="inline-flex p-4 rounded-2xl bg-blue-500/10 text-blue-400 text-3xl animate-bounce">
      ⚡
    </div>
    <h3 class="text-xl font-bold text-white">AI Agents are Building Your Website</h3>
    <p class="text-xs text-slate-400 leading-relaxed">The Architect, Designer, and Backend agents are currently generating custom layouts, typography, and React components for your new idea...</p>
    <div class="w-48 h-1.5 bg-slate-800 rounded-full mx-auto overflow-hidden">
      <div class="w-full h-full bg-gradient-to-r from-blue-500 to-emerald-400 animate-pulse"></div>
    </div>
  </div>
</body>
</html>""")

    if not code:
        # Fallback to reading the latest App.jsx only if idle
        sites = glob.glob("../generated-sites/*/frontend/src/App.jsx")
        if sites:
            latest_file = max(sites, key=os.path.getmtime)
            try:
                with open(latest_file, "r", encoding="utf-8") as f:
                    code = f.read()
            except Exception:
                pass

    if not code:
        return HTMLResponse("<html><body style='color:#fff;background:#0F172A;font-family:sans-serif;padding:60px;text-align:center'><h2>No website generated yet.</h2><p style='color:#94a3b8'>Fill out the form in the dashboard and click 'Generate Website' to preview it here.</p></body></html>")
        
    return HTMLResponse(build_preview_html(code))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
