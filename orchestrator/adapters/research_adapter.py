from pathlib import Path


RESEARCH_OUTPUT_DIR = Path("outputs/research")


def find_latest_research():
    files = sorted(
        RESEARCH_OUTPUT_DIR.glob("research_*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not files:
        raise FileNotFoundError("No research report found.")

    latest = files[0]

    if not latest.exists():
        raise FileNotFoundError(f"Research report missing: {latest}")

    if latest.stat().st_size == 0:
        raise ValueError(f"Research report is empty: {latest}")

    return latest


def get_latest_research():
    return find_latest_research()
