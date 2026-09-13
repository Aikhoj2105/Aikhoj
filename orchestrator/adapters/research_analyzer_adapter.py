"""
AI Khoj — Research Analyzer Adapter v2

Purpose:
Provide a stable file-based interface between the
Article Extractor and Research Analyzer.
"""

from pathlib import Path

from agents import research_analyzer_v2
from orchestrator.adapters.article_extractor_adapter import (
    extract_source_url,
)


ARTICLE_OUTPUT_DIR = Path("outputs/articles")


def find_latest_article():
    """Find the latest extracted article file."""

    files = sorted(
        ARTICLE_OUTPUT_DIR.glob("article_*.txt"),
        key=lambda path: path.stat().st_mtime,
    )

    if not files:
        raise FileNotFoundError(
            "No extracted article found in outputs/articles."
        )

    return files[-1]


def read_article_file(article_file):
    """Read an extracted article file."""

    article_file = Path(article_file)

    article_text = article_file.read_text(
        encoding="utf-8"
    )

    if not article_text.strip():
        raise ValueError(
            f"Article file is empty: {article_file}"
        )

    return article_text


def analyze_from_research(research_file):
    """Analyze the latest article and persist the analysis output."""

    article_file = find_latest_article()
    article_text = read_article_file(article_file)
    source_url = extract_source_url(research_file)

    analysis_text = research_analyzer_v2.analyze_article(
        article_text,
        source_url,
    )

    return save_analysis(analysis_text)

ANALYSIS_OUTPUT_DIR = Path("outputs/analysis")


def save_analysis(analysis_text):
    """Save generated analysis text to the analysis output directory."""
    if not analysis_text or not analysis_text.strip():
        raise ValueError("Analysis text is empty.")

    ANALYSIS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = ANALYSIS_OUTPUT_DIR / f"analysis_{timestamp}.md"
    output_file.write_text(analysis_text, encoding="utf-8")

    return output_file

def analyze_article(article_text, source_url):
    """Direct analysis kept for compatibility."""

    return research_analyzer_v2.analyze_article(
        article_text,
        source_url,
    )
