"""
AI Khoj — Article Extractor Adapter v3

Purpose:
Bridge the Research Report and Article Extractor,
then persist the extracted article as a stable file.
"""

import re
from datetime import datetime
from pathlib import Path

from agents import article_extractor


ARTICLE_OUTPUT_DIR = Path("outputs/articles")


def extract_source_url(research_file):
    """Extract the source URL from an AI Khoj research report."""

    research_file = Path(research_file)
    text = research_file.read_text(encoding="utf-8")

    match = re.search(
        r"^\*\*Source:\*\*\s*(https?://\S+)",
        text,
        re.MULTILINE,
    )

    if not match:
        raise ValueError(
            f"Source URL not found in research report: {research_file}"
        )

    return match.group(1)


def extract_from_research(research_file):
    """Extract article text from the research source URL."""

    source_url = extract_source_url(research_file)

    article_text = article_extractor.extract_article(source_url)

    if not article_text:
        raise ValueError("Article extraction returned empty text.")

    return article_text


def save_article(article_text):
    """Save extracted article text and return its file path."""

    ARTICLE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_path = (
        ARTICLE_OUTPUT_DIR
        / f"article_{timestamp}.txt"
    )

    output_path.write_text(
        article_text,
        encoding="utf-8",
    )

    return output_path


def extract_and_save_from_research(research_file):
    """Extract an article from research and save it as a stable file."""

    article_text = extract_from_research(research_file)

    return save_article(article_text)


def extract_article(url):
    """Direct URL extraction kept for compatibility."""

    return article_extractor.extract_article(url)
