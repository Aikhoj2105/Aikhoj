import os
import json
import urllib.request
import xml.etree.ElementTree as ET

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-3.5-flash"

if not API_KEY:
    print("❌ GEMINI_API_KEY नहीं मिली")
    exit()

# --------------------------------
# STEP 1: Get AI topics from RSS
# --------------------------------

RSS_URL = "https://blog.google/technology/ai/rss/"

try:
    request = urllib.request.Request(
        RSS_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        rss_data = response.read()

    root = ET.fromstring(rss_data)

    topics = []

    for item in root.iter("item"):
        title = item.findtext("title")

        if title:
            topics.append(title)

        if len(topics) >= 5:
            break

except Exception as e:
    print("❌ RSS Error:", e)
    exit()


# --------------------------------
# STEP 2: Send topics to Gemini
# --------------------------------

topic_list = "\n".join(
    f"{i+1}. {topic}"
    for i, topic in enumerate(topics)
)

prompt = f"""
You are the AI Khoj YouTube Research Assistant.

AI Khoj is a Hindi/Hinglish YouTube channel about:
- AI Agents
- Hidden AI Tools
- AI productivity
- AI se realistic earning opportunities
- New AI technology

Here are 5 latest AI topics collected from an RSS source:

{topic_list}

Analyze every topic.

For EACH topic give:

1. Topic
2. Simple Hinglish explanation
3. Curiosity Score /10
4. Usefulness Score /10
5. Freshness Score /10
6. YouTube Potential /10
7. AI Khoj Relevance /10
8. Final Score /10
9. Suggested Hindi/Hinglish video title

Then rank all 5 topics from BEST to WORST.

Finally tell me:

🏆 BEST TOPIC:
🥈 SECOND BEST:
🥉 THIRD BEST:

Be realistic.
Do not exaggerate.
Do not invent facts that are not present in the topic headline.
"""

url = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent?key={API_KEY}"
)

data = {
    "contents": [
        {
            "parts": [
                {
                    "text": prompt
                }
            ]
        }
    ]
}

request = urllib.request.Request(
    url,
    data=json.dumps(data).encode("utf-8"),
    headers={
        "Content-Type": "application/json"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(
            response.read().decode("utf-8")
        )

    answer = result["candidates"][0]["content"]["parts"][0]["text"]

    print("\n🤖 AI KHOJ RESEARCH AGENT v3")
    print("=" * 55)
    print(answer)

except urllib.error.HTTPError as e:
    print("\n❌ Gemini HTTP Error:", e.code)
    print(e.read().decode())

except Exception as e:
    print("\n❌ Error:", e)
