import ast
import os
import re

log_path = r'C:\Users\Laptop valley\.gemini\antigravity\brain\552db0d6-2595-4a28-97e4-ae94937b8855\.system_generated\tasks\task-601.log'
with open(log_path, 'r', encoding='utf-8') as f:
    log_content = f.read()

design_match = re.search(r"\{'design': \{'frontend_code': (.*?), 'current_stage': 'coding_backend'\}\}", log_content, re.DOTALL)
if design_match:
    frontend_code = ast.literal_eval(design_match.group(1))
else:
    print('Could not find frontend_code')

backend_match = re.search(r"\{'backend': \{'backend_code': (.*?), 'current_stage': 'reviewing'\}\}", log_content, re.DOTALL)
if backend_match:
    backend_code = ast.literal_eval(backend_match.group(1))
else:
    print('Could not find backend_code')

if design_match and backend_match:
    base_dir = r'E:\AI Website Builder Agent\generated-sites\a_modern_b2b_s'
    frontend_dir = os.path.join(base_dir, 'frontend', 'src')
    backend_dir = os.path.join(base_dir, 'backend')
    
    os.makedirs(frontend_dir, exist_ok=True)
    os.makedirs(backend_dir, exist_ok=True)
    
    with open(os.path.join(frontend_dir, 'App.jsx'), 'w', encoding='utf-8') as f:
        f.write(frontend_code)
        
    with open(os.path.join(backend_dir, 'server.js'), 'w', encoding='utf-8') as f:
        f.write(backend_code)
        
    with open(os.path.join(backend_dir, 'package.json'), 'w', encoding='utf-8') as f:
        f.write('{"name": "backend", "main": "server.js", "dependencies": {"express": "^4.18.2", "cors": "^2.8.5"}}')
        
    print('Successfully wrote files!')
