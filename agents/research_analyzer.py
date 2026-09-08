import os
import urllib.request
import urllib.parse
import json

MODEL = "gemini-3.5-flash"
API_KEY = os.getenv("GEMINI_API_KEY")


def analyze_article(article_text, source_url):
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY नहीं मिला.")

    prompt = f"""
You are the Research Analyzer for a Hindi/Hinglish YouTube channel called "AI Khoj".

Your job is to analyze the supplied article and convert it into useful research notes.

SOURCE URL:
{source_url}

ARTICLE TEXT:
{article_text}

Return the analysis in the following exact structure:

ARTICLE SUMMARY:
Write a simple 3-5 sentence summary.

KEY FACTS:
List the most important factual points from the article.

IMPORTANT CLAIMS:
List important claims made by the source.
Do not assume that every claim is independently verified.

WHY IT MATTERS:
Explain why this development could matter to normal people, businesses, developers, or the AI industry.

AI KHOJ ANGLES:
Suggest 3 interesting YouTube angles based only on the information provided.

POSSIBLE VIDEO TITLE:
Suggest 3 natural Hinglish YouTube titles. Avoid fake clickbait.

VERIFICATION NEEDED:
List claims, numbers, product names, dates, or technical statements that should be independently verified before publishing.

LIMITATIONS:
Mention important limitations or missing information in the article.

SOURCE QUALITY:
Give a simple rating:
High / Medium / Low

Explain briefly why you gave that rating.

IMPORTANT RULES:
- Do not invent information.
- Do not add facts that are not present in the supplied article.
- Clearly separate facts from claims.
- Do not treat the article's own claims as independently verified facts.
- If information is missing, say "Not provided in source".
- Keep the analysis useful for YouTube research.
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

    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["candidates"][0]["content"]["parts"][0]["text"]


def main():
    print("\n🧠 AI KHOJ — RESEARCH ANALYZER v1")
    print("=" * 55)

    source_url = input("\n🔗 Source URL: ").strip()

    if not source_url:
        print("❌ Source URL खाली है.")
        return

    print("\n📄 Article text paste करो.")
    print("Article खत्म होने के बाद नई line में:")
    print("END")
    print()

    lines = []

    while True:
        line = input()

        if line.strip() == "END":
            break

        lines.append(line)

    article_text = "\n".join(lines).strip()

    if not article_text:
        print("❌ Article text खाली है.")
        return

    print("\n🤖 Gemini article analyze कर रहा है...")
    print("Please wait...\n")

    try:
        analysis = analyze_article(article_text, source_url)

        print("=" * 55)
        print(analysis)
        print("=" * 55)
        print("\n✅ Research analysis complete!")

    except Exception as e:
        print("\n❌ Error:", e)


if __name__ == "__main__":
    main()
