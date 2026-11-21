import os, json, urllib.request
from dotenv import load_dotenv

load_dotenv()
req = urllib.request.Request(
    "https://api.groq.com/openai/v1/models",
    headers={
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "User-Agent": "text2sql-app/1.0",
    },
)
with urllib.request.urlopen(req) as r:
    for m in json.loads(r.read())["data"]:
        print(m["id"])