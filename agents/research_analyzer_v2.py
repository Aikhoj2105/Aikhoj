import os
import urllib.request
import urllib.parse
import json
from datetime import datetime

MODEL = "gemini-3.5-flash"
API_KEY = os.getenv("GEMINI_API_KEY")


def analyze_article(article_text, source_url):
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY नहीं मिला.")

    prompt = f"""
You are the Research Analyzer for a Hindi/Hinglish YouTube channel called "AI Khoj".

Analyze the supplied article and convert it into useful YouTube research notes.

SOURCE URL:
{source_url}

ARTICLE TEXT:
{article_text}

Return the analysis in this exact structure:

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
Suggest 3 interesting YouTube angles based only on the article.

POSSIBLE VIDEO TITLE:
Suggest 3 natural Hinglish YouTube titles. Avoid fake clickbait.

VERIFICATION NEEDED:
List claims, numbers, product names, dates, or technical statements that should be independently verified before publishing.

LIMITATIONS:
Mention important limitations or missing information in the article.

SOURCE QUALITY:
Give a rating:
High / Medium / Low

Explain briefly why.

IMPORTANT RULES:
- Do not invent information.
- Do not add facts that are not present in the article.
- Clearly separate facts from claims.
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


def read_article_file():
    folder = "outputs/articles"

    if not os.path.exists(folder):
        raise FileNotFoundError(
            "outputs/articles folder नहीं मिला. "
            "पहले Article Extractor v2 चलाएं."
        )

    files = [
        f for f in os.listdir(folder)
        if f.endswith(".txt")
    ]

    if not files:
        raise FileNotFoundError(
            "कोई article file नहीं मिली. "
            "पहले Article Extractor v2 चलाएं."
        )

    files.sort(
        key=lambda f: os.path.getmtime(os.path.join(folder, f)),
        reverse=True
    )

    latest_file = os.path.join(folder, files[0])

    with open(latest_file, "r", encoding="utf-8") as file:
        content = file.read()

    source_url = ""

    if content.startswith("SOURCE URL:"):
        first_line = content.splitlines()[0]
        source_url = first_line.replace("SOURCE URL:", "").strip()

    separator = "=" * 70

    if separator in content:
        article_text = content.split(separator, 1)[1].strip()
    else:
        article_text = content

    return latest_file, source_url, article_text


def save_analysis(analysis, source_url):
    os.makedirs("outputs/research", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"outputs/research/research_{timestamp}.md"

    with open(filename, "w", encoding="utf-8") as file:
        file.write("# AI Khoj Research Report\n\n")
        file.write(f"**Source:** {source_url}\n\n")
        file.write("---\n\n")
        file.write(analysis)

    return filename


def main():
    print("\n🧠 AI KHOJ — RESEARCH ANALYZER v2")
    print("=" * 55)

    try:
        filename, source_url, article_text = read_article_file()

        print(f"\n📄 Latest article:")
        print(filename)

        print(f"\n🔗 Source:")
        print(source_url)

        print(f"\n📊 Article characters: {len(article_text)}")

        if not article_text.strip():
            print("\n❌ Article text खाली है.")
            return

        print("\n🤖 Gemini article analyze कर रहा है...")
        print("Please wait...\n")

        analysis = analyze_article(article_text, source_url)

        print("=" * 55)
        print(analysis)
        print("=" * 55)

        report_file = save_analysis(analysis, source_url)

        print("\n✅ Research analysis complete!")
        print(f"💾 Research report saved to:")
        print(report_file)

    except Exception as e:
        print("\n❌ Error:")
        print(e)


if __name__ == "__main__":
    main()
