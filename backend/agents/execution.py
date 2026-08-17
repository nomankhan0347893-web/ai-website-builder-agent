import subprocess
import os
import tempfile

def execution_node(state):
    """
    Prepares terminal commands to write the generated code and assets.
    """
    print("--- EXECUTION NODE (Preparing Commands) ---")
    
    import re
    
    raw_name = state.get("business_description", "demo_site")[:15].strip().replace(" ", "_").lower()
    business_name = re.sub(r'[^a-z0-9_]', '', raw_name)
    
    base_dir = f"../generated-sites/{business_name}"
    frontend_dir = f"{base_dir}/frontend/src"
    backend_dir = f"{base_dir}/backend"
    
    # 1. Write host.py directly to the frontend directory
    host_py_content = r'''import os
import http.server
import socketserver
import webbrowser
import re
import threading

base_dir = os.path.dirname(os.path.abspath(__file__))
app_jsx_path = os.path.join(base_dir, "src", "App.jsx")

try:
    with open(app_jsx_path, "r", encoding="utf-8") as f:
        app_code = f.read()
except FileNotFoundError:
    app_code = "export default function App() { return <div>App.jsx not found</div> }"

def replace_unsplash(match):
    width_height = match.group(1)
    width, height = width_height.split('x')
    return f"https://picsum.photos/seed/{match.group(2)[:10]}/{width}/{height}"

app_code = re.sub(r"https://source\.unsplash\.com/(\d+x\d+)/\?([^\"']+)", replace_unsplash, app_code)

# Strip exports so Babel runs it in script scope without ReferenceError: exports is not defined
app_code = re.sub(r'export\s+default\s+function\s+App', 'function App', app_code)
app_code = re.sub(r'export\s+function\s+App', 'function App', app_code)
app_code = re.sub(r'export\s+default\s+App\s*;?', '', app_code)

html_template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Generated Website</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script type="importmap">
    {
      "imports": {
        "react": "https://esm.sh/react@18.2.0",
        "react-dom/client": "https://esm.sh/react-dom@18.2.0/client",
        "lucide-react": "https://esm.sh/lucide-react@0.263.1?deps=react@18.2.0"
      }
    }
  </script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel" data-type="module">
    import { createRoot } from 'react-dom/client';
    
__APP_CODE_PLACEHOLDER__

    createRoot(document.getElementById('root')).render(<App />);
  </script>
</body>
</html>
"""

html_content = html_template.replace("__APP_CODE_PLACEHOLDER__", app_code)

index_html_path = os.path.join(base_dir, "index.html")
with open(index_html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=base_dir, **kwargs)

def kill_port_5174():
    try:
        cmd = 'powershell -Command "Get-NetTCPConnection -LocalPort 5174 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"'
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

kill_port_5174()

port = 5174
httpd = None
try:
    httpd = socketserver.TCPServer(("", 5174), Handler)
except OSError:
    httpd = socketserver.TCPServer(("", 0), Handler)
    port = httpd.server_address[1]

if httpd:
    print(f"Serving frontend at port {port}")
    def open_browser():
        webbrowser.open(f"http://localhost:{port}")
    threading.Timer(1.0, open_browser).start()
    httpd.serve_forever()
'''

    abs_frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", frontend_dir))
    os.makedirs(abs_frontend_dir, exist_ok=True)
    host_py_path = os.path.join(abs_frontend_dir, "..", "host.py")
    with open(host_py_path, "w", encoding="utf-8") as f:
        f.write(host_py_content)

    # 2. Create a safe Python writer script in a temporary location
    writer_script = f"""
import os

frontend_dir = r"{frontend_dir}"
backend_dir = r"{backend_dir}"

os.makedirs(frontend_dir, exist_ok=True)
os.makedirs(backend_dir, exist_ok=True)

with open(os.path.join(frontend_dir, "App.jsx"), "w", encoding="utf-8") as f:
    f.write(r'''{state.get("frontend_code", "")}''')

with open(os.path.join(backend_dir, "server.js"), "w", encoding="utf-8") as f:
    f.write(r'''{state.get("backend_code", "")}''')

with open(os.path.join(backend_dir, "package.json"), "w", encoding="utf-8") as f:
    f.write('{{"name": "backend", "main": "server.js", "dependencies": {{"express": "^4.18.2", "cors": "^2.8.5"}}}}')

print("Files successfully generated.")
"""
    
    script_path = os.path.join(tempfile.gettempdir(), "write_agent_files.py")
    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(writer_script)
    except Exception as e:
        print(f"Error creating temp writer script: {e}")

    frontend_base = f"{base_dir}/frontend"
    # Launch host.py in a detached new console window
    launch_host_cmd = f"cd {frontend_base} && python -c \"import subprocess; subprocess.Popen(['python', 'host.py'], creationflags=subprocess.CREATE_NEW_CONSOLE)\""

    commands = [
        f"python {script_path}",
        launch_host_cmd,
        f"cd {base_dir} && git init",
        f"cd {base_dir} && git add .",
        f"cd {base_dir} && git commit -m \"Checkpoint: Approved generated site\""
    ]
    
    return {"pending_commands": commands, "current_stage": "awaiting_approval"}

def run_commands_node(state):
    """
    Executes the terminal commands ONLY IF human_approval is True.
    """
    print("--- RUN COMMANDS NODE ---")
    
    if not state.get("human_approval"):
        print("Execution denied by human. Skipping commands.")
        return {"current_stage": "denied"}
        
    for cmd in state.get("pending_commands", []):
        print(f"Executing: {cmd}")
        # In a real deployed app, this runs the shell command
        subprocess.run(cmd, shell=True)
        
    return {"current_stage": "completed", "pending_commands": []}
