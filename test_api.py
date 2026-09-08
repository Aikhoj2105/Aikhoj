import os
import json
import urllib.request

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-3.5-flash"

url = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent?key={API_KEY}"
)

data = {
    "contents": [
        {
            "parts": [
                {
                    "text": "Reply with exactly: AI Khoj API is working!"
                }
            ]
        }
    ]
}

request = urllib.request.Request(
    url,
    data=json.dumps(data).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read().decode("utf-8"))

    print(result["candidates"][0]["content"]["parts"][0]["text"])

except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print(e.read().decode())
