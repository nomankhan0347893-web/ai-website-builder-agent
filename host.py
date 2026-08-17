import os
import http.server
import socketserver
import webbrowser
import re
import threading

base_dir = r"E:\AI Website Builder Agent\generated-sites\a_modern_b2b_s\frontend"
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

with socketserver.TCPServer(("", 0), Handler) as httpd:
    port = httpd.server_address[1]
    print(f"Serving frontend at port {port}")
    def open_browser():
        webbrowser.open(f"http://localhost:{port}")
    threading.Timer(1.0, open_browser).start()
    httpd.serve_forever()
