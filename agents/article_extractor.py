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
    # Remove scripts and styles
    html = re.sub(
        r"<(script|style).*?>.*?</\1>",
        " ",
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Remove HTML comments
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)

    # Remove remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", html)

    # Decode HTML entities
    text = unescape(text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


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

        print("\n📄 Extracted text:")
        print("=" * 60)
        print(text[:5000])
        print("=" * 60)

        print(f"\n✅ Characters extracted: {len(text)}")

    except Exception as e:
        print("\n❌ Error:", e)


if __name__ == "__main__":
    main()
