import urllib.request
import xml.etree.ElementTree as ET

URL = "https://blog.google/technology/ai/rss/"


def fetch_rss():
    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        data = response.read()

    return data


def parse_rss(data, limit=5):
    root = ET.fromstring(data)

    articles = []

    for item in root.iter("item"):
        title = item.findtext("title")
        link = item.findtext("link")
        description = item.findtext("description")
        pub_date = item.findtext("pubDate")

        if title:
            articles.append({
                "title": title.strip(),
                "link": link.strip() if link else "",
                "description": description.strip() if description else "",
                "pub_date": pub_date.strip() if pub_date else ""
            })

        if len(articles) >= limit:
            break

    return articles


def main():
    print("\n🌐 AI KHOJ RSS RESEARCH v2")
    print("=" * 50)

    try:
        data = fetch_rss()
        articles = parse_rss(data)

        if not articles:
            print("❌ कोई RSS article नहीं मिला")
            return

        for i, article in enumerate(articles, 1):
            print(f"\n📰 Article {i}")
            print(f"Title: {article['title']}")
            print(f"Date: {article['pub_date']}")
            print(f"Link: {article['link']}")
            print(f"Description: {article['description'][:300]}...")

        print("\n" + "=" * 50)
        print(f"✅ Total articles collected: {len(articles)}")

    except Exception as e:
        print("❌ Error:", e)


if __name__ == "__main__":
    main()
