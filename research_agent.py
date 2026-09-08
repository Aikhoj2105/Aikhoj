import os
import json
import urllib.request

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("❌ GEMINI_API_KEY नहीं मिली")
    exit()

MODEL = "gemini-3.5-flash"

url = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent"
)

topic = input("\n🔎 किस AI topic पर research करनी है?\n> ")

prompt = f"""
You are the AI Khoj Research Agent.

You are researching content for a Hindi/Hinglish YouTube channel called "AI Khoj".

Research this topic using current web information:

TOPIC:
{topic}

Give the result in this exact structure:

1. 🔥 Topic Summary
Explain the topic simply in Hinglish.

2. 📌 Important Facts
Give 5 important factual points.

3. 🧪 Real Examples
Give real-world examples or products related to this topic.

4. ⚠️ Reality Check
Clearly separate confirmed facts from claims, hype, or uncertainty.

5. 🎬 YouTube Potential
Give a score from 1-10 for:
- Curiosity
- Usefulness
- Freshness
- Viral potential

6. 🏆 Final Score
Give an overall score out of 10.

7. 🔗 Sources
List the important sources you used with their names and URLs.

Do not invent sources.
Prefer official documentation and reliable sources.
Use current information whenever possible.
"""

data = {
    "contents": [
        {
            "parts": [
                {"text": prompt}
            ]
        }
    ],
    "tools": [
        {
            "google_search": {}
        }
    ]
}

request = urllib.request.Request(
    url,
    data=json.dumps(data).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "x-goog-api-key": API_KEY
    },
    method="POST"
)

try:
    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read().decode("utf-8"))

    answer = result["candidates"][0]["content"]["parts"][0]["text"]

    print("\n🤖 AI KHOJ RESEARCH AGENT v2")
    print("=" * 50)
    print(answer)

    print("\n" + "=" * 50)
    print("🌐 WEB RESEARCH COMPLETE")

except Exception as e:
    print("\n❌ Error:", e)

