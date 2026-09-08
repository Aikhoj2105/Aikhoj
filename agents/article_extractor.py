import urllib.request
import re
from html import unescape

USER_AGENT = "Mozilla/5.0 (Android) AIKhoj/1.0"


def fetch_page(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="ignore")


def clean_html(html):
    # Remove comments
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)

    # Remove scripts, styles and other non-content elements
    html = re.sub(
        r"<(script|style|noscript|svg|nav|footer|header).*?>.*?</\1>",
        " ",
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Convert common block-level tags into line breaks
    html = re.sub(
        r"</(p|div|article|section|h1|h2|h3|h4|li|blockquote)>",
        "\n",
        html,
        flags=re.IGNORECASE
    )

    # Remove remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", html)

    # Decode HTML entities
    text = unescape(text)

    # Clean whitespace line-by-line
    lines = []

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if len(line) >= 30:
            lines.append(line)

    # Remove duplicate consecutive lines
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


def main():
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

    except Exception as e:
        print("\n❌ Error:", e)


if __name__ == "__main__":
    main()
