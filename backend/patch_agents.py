import os
import glob

agent_dir = r"e:\AI Website Builder Agent\backend\agents"
for py_file in glob.glob(os.path.join(agent_dir, "*.py")):
    with open(py_file, "r") as f:
        content = f.read()
    
    new_content = content.replace(
        "content = response.content.strip()", 
        "content = (response.content[0].get('text', '') if isinstance(response.content, list) else response.content).strip()"
    ).replace(
        "code = response.content.strip()",
        "code = (response.content[0].get('text', '') if isinstance(response.content, list) else response.content).strip()"
    )
    
    if new_content != content:
        with open(py_file, "w") as f:
            f.write(new_content)
        print(f"Patched {py_file}")
