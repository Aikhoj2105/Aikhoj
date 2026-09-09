import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
import re
from html import unescape

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "core")
)

from gemini_client import generate_text


RSS_URL = "https://blog.google/technology/ai/rss/"
USER_AGENT = "Mozilla/5.0 (Android) AIKhoj/1.0"


def fetch_rss():
    request = urllib.request.Request(
        RSS_URL,
        headers={"User-Agent": USER_AGENT}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def parse_rss(data, limit=10):
    root = ET.fromstring(data)
    articles = []

    for item in root.iter("item"):
        title = item.findtext("title")
        link = item.findtext("link")
        description = item.findtext("description")

        if title and link:
            articles.append({
                "title": title.strip(),
                "link": link.strip(),
                "description": description.strip()
                if description else ""
            })

        if len(articles) >= limit:
            break

    return articles


def read_latest_research():
    folder = "outputs/research"

    if not os.path.exists(folder):
        raise FileNotFoundError(
            "outputs/research folder नहीं मिला."
        )

    files = [
        f for f in os.listdir(folder)
        if f.endswith(".md")
    ]

    if not files:
        raise FileNotFoundError(
            "कोई research report नहीं मिली."
        )

    files.sort(
        key=lambda f: os.path.getmtime(
            os.path.join(folder, f)
        ),
        reverse=True
    )

    latest = os.path.join(folder, files[0])

    with open(latest, "r", encoding="utf-8") as file:
        return latest, file.read()


def extract_claims(research_report):
    prompt = f"""
You are a claim extraction assistant for AI Khoj.

From the following research report, extract only claims
that should be cross-checked against original sources.

RESEARCH REPORT:
{research_report}

Return ONLY a numbered list.

For every claim include:

CLAIM:
TYPE:
SEARCH KEYWORDS:

Types can include:
- Product
- Version
- Statistic
- Date
- Cost
- Performance
- Company claim
- Technical
- Other

Rules:
- Do not invent claims.
- Keep each claim short.
- Extract factual or potentially factual claims.
- Do not include opinions.
- Do not include YouTube title ideas.
"""

    return generate_text(prompt)


def clean_html(html):
    html = re.sub(
        r"<!--.*?-->",
        " ",
        html,
        flags=re.DOTALL
    )

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


def fetch_article(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        html = response.read().decode(
            "utf-8",
            errors="ignore"
        )

    return clean_html(html)


def select_sources(claims, rss_articles):
    sources_text = ""

    for i, article in enumerate(rss_articles, 1):
        sources_text += f"""
SOURCE {i}
TITLE: {article['title']}
URL: {article['link']}
DESCRIPTION: {article['description']}
"""

    prompt = f"""
You are a source matching assistant for AI Khoj.

CLAIMS:
{claims}

AVAILABLE RSS SOURCES:
{sources_text}

For each claim, identify the most relevant source number.

Return ONLY this format:

CLAIM 1: SOURCE 1
CLAIM 2: SOURCE 1
CLAIM 3: NO_RELEVANT_SOURCE

Rules:
- Only select from provided sources.
- Do not invent sources.
- If no relevant source exists, use NO_RELEVANT_SOURCE.
"""

    return generate_text(prompt)


def parse_source_numbers(source_matches):
    numbers = set()

    matches = re.findall(
        r"SOURCE\s+(\d+)",
        source_matches,
        flags=re.IGNORECASE
    )

    for number in matches:
        try:
            numbers.add(int(number))
        except ValueError:
            pass

    return sorted(numbers)


def fact_check(claims, source_evidence):
    prompt = f"""
You are the Fact Checker Agent for the Hindi/Hinglish
YouTube channel "AI Khoj".

Compare the claims against the supplied original-source
evidence.

CLAIMS:
{claims}

SOURCE EVIDENCE:
{source_evidence}

For every claim return:

CLAIM:
STATUS:
EVIDENCE:
SOURCE:
RECOMMENDATION:

STATUS must be exactly one of:

SUPPORTED
CONFLICTING
NOT ENOUGH EVIDENCE

Rules:
- Do not invent evidence.
- Do not use outside knowledge.
- SUPPORTED means the supplied source directly supports
  the claim.
- CONFLICTING means the supplied source contradicts it.
- NOT ENOUGH EVIDENCE means the source lacks enough
  information.
- A company statement remains a company statement.
- Do not call a company claim independently verified.
- Numbers, dates, versions, prices, and performance claims
  without direct evidence must be NOT ENOUGH EVIDENCE.
"""

    return generate_text(prompt)


def main():
    print("\n🛡️ AI KHOJ — FACT CHECKER v1.1")
    print("=" * 60)

    try:
        research_file, research_report = read_latest_research()

        print("\n📄 Research report:")
        print(research_file)

        print("\n🔍 Extracting claims...")

        claims = extract_claims(research_report)

        print("\n📋 Claims identified:")
        print(claims)

        print("\n🌐 Reading RSS sources...")

        rss_data = fetch_rss()
        rss_articles = parse_rss(rss_data)

        print(
            f"✅ {len(rss_articles)} RSS sources available."
        )

        print("\n🔎 Matching claims with sources...")

        source_matches = select_sources(
            claims,
            rss_articles
        )

        print("\n📌 Source matches:")
        print(source_matches)

        source_numbers = parse_source_numbers(
            source_matches
        )

        print("\n🔢 Sources selected:")
        print(source_numbers)

        if not source_numbers:
            print(
                "\n❌ कोई source select नहीं हुआ."
            )
            return

        print("\n📄 Fetching source evidence...")

        evidence = ""

        for source_number in source_numbers:

            if source_number < 1:
                continue

            if source_number > len(rss_articles):
                print(
                    f"⚠️ Source {source_number} उपलब्ध नहीं है."
                )
                continue

            article = rss_articles[
                source_number - 1
            ]

            print(
                f"\n🔗 Source {source_number}:"
            )
            print(article["title"])
            print(article["link"])

            try:
                text = fetch_article(
                    article["link"]
                )

                if not text.strip():
                    print(
                        f"⚠️ Source {source_number} खाली है."
                    )
                    continue

                evidence += f"""
SOURCE {source_number}
TITLE: {article['title']}
URL: {article['link']}

ARTICLE EVIDENCE:
{text[:12000]}

----------------------------------------
"""

                print(
                    f"✅ Source {source_number} extracted "
                    f"({len(text)} characters)"
                )

            except Exception as e:
                print(
                    f"⚠️ Source {source_number} failed: {e}"
                )

        if not evidence.strip():
            print(
                "\n❌ कोई source evidence नहीं मिला."
            )
            return

        print(
            "\n🤖 Comparing claims with evidence..."
        )

        result = fact_check(
            claims,
            evidence
        )

        print("\n" + "=" * 60)
        print("🛡️ FACT CHECK RESULT")
        print("=" * 60)

        print(result)

        print("=" * 60)
        print("\n✅ Fact Check complete!")

    except Exception as e:
        print("\n❌ Error:")
        print(e)


if __name__ == "__main__":
    main()
