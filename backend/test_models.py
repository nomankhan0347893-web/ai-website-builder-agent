import os
from dotenv import load_dotenv
import requests

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("NO API KEY FOUND")
else:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    resp = requests.get(url)
    if resp.status_code == 200:
        models = resp.json().get("models", [])
        names = [m["name"].replace("models/", "") for m in models if "gemini" in m["name"].lower()]
        print("AVAILABLE GEMINI MODELS:")
        for name in names:
            print("-", name)
    else:
        print("ERROR:", resp.text)
