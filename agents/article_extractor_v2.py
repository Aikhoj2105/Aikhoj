import urllib.request
import re
from html import unescape
from datetime import datetime
import os

USER_AGENT = "Mozilla/5.0 (Android) AIKhoj/1.0"


def fetch_page(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="ignore")


def clean_html(html):
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)

    html = re.sub(
        r"<(script|style|noscript|svg|nav|footer|header).*?>.*?</\1>",
        " ",
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    html = re.sub(
        r"</(p|div|article|section|h1|h2|h3|h4|li|blockquote)>",
        "\n",
        html,
        flags=re.IGNORECASE
    )

    text = re.sub(r"<[^>]+>", " ", html)

    text = unescape(text)

    lines = []

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if len(line) >= 30:
            lines.append(line)

    cleaned = []

    for line in lines:
        if not cleaned or line != cleaned[-1]:
            cleaned.append(line)

    return "\n".join(cleaned)


def extract_article(url):
    print("\n🌐 Opening article...")
    print(url)

    html = fetch_page(url)
    text = clean_html(html)

    return text


def save_article(text, url):
    os.makedirs("outputs/articles", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"outputs/articles/article_{timestamp}.txt"

    with open(filename, "w", encoding="utf-8") as file:
        file.write(f"SOURCE URL:\n{url}\n\n")
        file.write("=" * 70 + "\n\n")
        file.write(text)

    return filename


def main():
    print("\n🌐 AI KHOJ — ARTICLE EXTRACTOR v2")
    print("=" * 55)

    url = input("\n🔗 Article URL: ").strip()

    if not url:
        print("❌ URL खाली है.")
        return

    try:
        text = extract_article(url)

        print("\n📄 Cleaned article text:")
        print("=" * 60)
        print(text[:5000])
        print("=" * 60)

        print(f"\n✅ Characters extracted: {len(text)}")

        filename = save_article(text, url)

        print(f"\n💾 Article saved to:")
        print(filename)

    except Exception as e:
        print("\n❌ Error:")
        print(e)


if __name__ == "__main__":
    main()
