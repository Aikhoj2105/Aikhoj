import os
import urllib.request
import urllib.parse
import json
from datetime import datetime

MODEL = "gemini-3.5-flash"
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ GEMINI_API_KEY नहीं मिला.")
    print("पहले export GEMINI_API_KEY='your-key' चलाएं.")
    exit()

topic = input("\n🎯 Video Topic: ").strip()

if not topic:
    print("❌ Topic खाली नहीं हो सकता.")
    exit()

prompt = f"""
You are the Script Writer Agent for a Hindi/Hinglish YouTube channel called "AI Khoj".

Channel tagline:
"AI की वो जानकारी जो आसानी से नहीं मिलती।"

Write a high-quality 8-10 minute faceless YouTube video script on:

TOPIC:
{topic}

Target audience:
Beginners to intermediate AI users.

Language:
Natural Hinglish using simple Hindi + commonly used English AI/tech terms.

Script structure:

1. HOOK
- 20-30 seconds
- Create curiosity immediately
- Do not use fake or exaggerated claims

2. INTRO
- Introduce the topic and why it matters

3. MAIN EXPLANATION
- Explain the concept simply
- Use relatable examples

4. PRACTICAL EXAMPLES
- Show how a normal person could actually use it

5. EXPERIMENT / DEMO
- Suggest a practical screen-recording demonstration

6. REALITY CHECK
- Explain limitations, risks, costs, or things that may not work
- Never promise guaranteed results

7. FINAL TAKEAWAY
- Summarize the important points

8. CTA
- Natural YouTube CTA
- Encourage viewers to subscribe to AI Khoj

Also include [B-ROLL] and [SCREEN RECORDING] suggestions wherever useful.

Important rules:
- Do not invent statistics, features, prices, or claims.
- Clearly mark anything that needs verification.
- No unnecessary repetition.
- Keep the script engaging and conversational.
- The final script should be ready for voice-over.
"""

url = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent?key={urllib.parse.quote(API_KEY)}"
)

data = {
    "contents": [
        {
            "parts": [
                {"text": prompt}
            ]
        }
    ]
}

try:
    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.loads(response.read().decode("utf-8"))

    script = result["candidates"][0]["content"]["parts"][0]["text"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"outputs/script_{timestamp}.md"

    os.makedirs("outputs", exist_ok=True)

    with open(filename, "w", encoding="utf-8") as file:
        file.write(f"# AI Khoj YouTube Script\n\n")
        file.write(f"**Topic:** {topic}\n\n")
        file.write("---\n\n")
        file.write(script)

    print("\n✅ Script successfully generated!")
    print(f"📄 Saved to: {filename}")

    print("\n" + "=" * 60)
    print(script)
    print("=" * 60)

except Exception as e:
    print("\n❌ Error:")
    print(e)
