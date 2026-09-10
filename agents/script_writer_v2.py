#!/usr/bin/env python3

"""
============================================================
AI KHOJ — SCRIPT WRITER v2
Block 1A — Foundation
============================================================
"""

from pathlib import Path
from datetime import datetime


FACT_CHECK_DIR = Path(
    "outputs/fact_check"
)

SCRIPT_OUTPUT_DIR = Path(
    "outputs/scripts"
)


def banner():
    print()
    print("=" * 60)
    print("AI KHOJ — SCRIPT WRITER v2")
    print("Block 1A — Foundation")
    print("=" * 60)


def log(message, level="INFO"):
    print(
        f"[{level}] {message}"
    )


def current_timestamp():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def ensure_output_folder():
    """
    Create the script output directory
    if it does not already exist.
    """

    SCRIPT_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    log(
        f"Script output folder ready: "
        f"{SCRIPT_OUTPUT_DIR}"
    )


def find_latest_fact_check():
    """
    Find the newest Fact Checker v3
    Markdown report.
    """

    if not FACT_CHECK_DIR.exists():
        log(
            f"Fact-check directory not found: "
            f"{FACT_CHECK_DIR}",
            "ERROR"
        )
        return None

    reports = sorted(
        FACT_CHECK_DIR.glob(
            "fact_check_*.md"
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True
    )

    if not reports:
        log(
            "No fact-check reports found.",
            "ERROR"
        )
        return None

    latest_report = reports[0]

    log(
        f"Latest fact-check report: "
        f"{latest_report}"
    )

    return latest_report


def read_fact_check_report(
    report_path
):
    """
    Read the selected fact-check report
    using UTF-8 encoding.
    """

    if report_path is None:
        return None

    try:
        text = report_path.read_text(
            encoding="utf-8"
        )
    except OSError as e:
        log(
            f"Could not read fact-check report: "
            f"{e}",
            "ERROR"
        )
        return None

    log(
        f"Fact-check report loaded: "
        f"{len(text)} characters"
    )

    return text


def main():
    banner()

    print()

    log(
        f"Started at: "
        f"{current_timestamp()}"
    )

    ensure_output_folder()

    report_path = find_latest_fact_check()

    if report_path is None:
        log(
            "Script Writer cannot continue "
            "without a fact-check report.",
            "ERROR"
        )
        return

    report_text = read_fact_check_report(
        report_path
    )

    if report_text is None:
        log(
            "Fact-check report could not be loaded.",
            "ERROR"
        )
        return

    print()
    print(
        f"Latest Fact Check:"
    )
    print(
        f"  {report_path.name}"
    )

    print(
        f"Characters Loaded:"
    )
    print(
        f"  {len(report_text)}"
    )

    print()
    log(
        "✅ Block 1A Foundation Ready"
    )


if __name__ == "__main__":
    main()
