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



# ============================================================
# Block 2 — Extract Script-Ready Claims
# ============================================================

def extract_script_ready_claims(report_text):
    """
    Extract script-ready claims from the Fact Checker v3 report.

    Only claims inside the 'Script-Ready Claims' section are returned.
    Additional safety checks require:
    - Status = SUPPORTED
    - Confidence = HIGH or MEDIUM
    """

    if not report_text:
        log(
            "Fact-check report text is empty.",
            "ERROR"
        )
        return []

    marker = "## Script-Ready Claims"

    if marker not in report_text:
        log(
            "Script-Ready Claims section not found.",
            "ERROR"
        )
        return []

    section = report_text.split(
        marker,
        1
    )[1]

    # Stop before the next major Markdown section.
    if "\n## " in section:
        section = section.split(
            "\n## ",
            1
        )[0]

    lines = section.splitlines()

    claims = []
    current = None

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("### Claim "):
            if current is not None:
                claims.append(current)

            claim_id_text = stripped[
                len("### Claim "):
            ].strip()

            try:
                claim_id = int(claim_id_text)
            except ValueError:
                current = None
                continue

            current = {
                "claim_id": claim_id,
                "claim": "",
                "priority": "MEDIUM",
                "status": "",
                "confidence": "",
                "source_ids": []
            }

        elif current is not None:

            if stripped.startswith("**Claim:**"):
                current["claim"] = stripped[
                    len("**Claim:**"):
                ].strip()

            elif stripped.startswith("**Priority:**"):
                current["priority"] = stripped[
                    len("**Priority:**"):
                ].strip().upper()

            elif stripped.startswith("**Status:**"):
                current["status"] = stripped[
                    len("**Status:**"):
                ].strip().upper()

            elif stripped.startswith("**Confidence:**"):
                current["confidence"] = stripped[
                    len("**Confidence:**"):
                ].strip().upper()

            elif stripped.startswith("**Source IDs:**"):
                value = stripped[
                    len("**Source IDs:**"):
                ].strip()

                value = value.strip("[]")

                if value:
                    source_ids = []

                    for item in value.split(","):
                        item = item.strip()

                        try:
                            source_ids.append(int(item))
                        except ValueError:
                            continue

                    current["source_ids"] = source_ids

    if current is not None:
        claims.append(current)

    # Final safety gate.
    script_ready = []

    for claim in claims:
        if claim.get("status") != "SUPPORTED":
            continue

        if claim.get("confidence") not in {
            "HIGH",
            "MEDIUM"
        }:
            continue

        if not claim.get("claim"):
            continue

        script_ready.append(claim)

    log(
        f"Script-ready claims extracted: "
        f"{len(script_ready)}"
    )

    return script_ready


def display_script_ready_claims(claims):
    """
    Display extracted script-ready claims
    in a compact readable format.
    """

    print()
    print("=" * 60)
    print("SCRIPT-READY CLAIMS")
    print("=" * 60)

    if not claims:
        print("No script-ready claims found.")
        return

    for item in claims:
        print()
        print(
            f"Claim ID: {item['claim_id']}"
        )
        print(
            f"Claim: {item['claim']}"
        )
        print(
            f"Priority: {item['priority']}"
        )
        print(
            f"Status: {item['status']}"
        )
        print(
            f"Confidence: {item['confidence']}"
        )
        print(
            f"Source IDs: {item['source_ids']}"
        )


# ============================================================
# Block 3A — Claim Priority Engine
# ============================================================

PRIORITY_SCORES = {
    "HIGH": 100,
    "MEDIUM": 70,
    "LOW": 40,
    "UNKNOWN": 10
}


def build_claim_priority(script_ready_claims):
    """
    Add priority scores and sort claims.
    """

    prioritized = []

    for item in script_ready_claims:

        claim = dict(item)

        priority = str(
            claim.get(
                "priority",
                "UNKNOWN"
            )
        ).strip().upper()

        score = PRIORITY_SCORES.get(
            priority,
            PRIORITY_SCORES["UNKNOWN"]
        )

        claim["priority"] = priority
        claim["priority_score"] = score

        prioritized.append(claim)

    prioritized.sort(
        key=lambda x: (
            x.get("priority_score", 0),
            -x.get("claim_id", 0)
        ),
        reverse=True
    )

    log(
        f"Prioritized claims: "
        f"{len(prioritized)}"
    )

    return prioritized


def display_claim_priority(prioritized_claims):
    """
    Display claim priority table.
    """

    print()
    print("=" * 60)
    print("CLAIM PRIORITY")
    print("=" * 60)

    if not prioritized_claims:
        print("No prioritized claims.")
        return

    for item in prioritized_claims:

        print()

        print(
            f"Claim {item['claim_id']}"
        )

        print(
            f"Priority : "
            f"{item['priority']}"
        )

        print(
            f"Score    : "
            f"{item['priority_score']}"
        )

    print()

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

    # --------------------------------------------------------
    # Block 2 — Extract Script-Ready Claims
    # --------------------------------------------------------

    script_ready_claims = extract_script_ready_claims(
        report_text
    )

    display_script_ready_claims(
        script_ready_claims
    )

    # --------------------------------------------------------
    # Block 3A — Claim Priority Engine
    # --------------------------------------------------------

    prioritized_claims = build_claim_priority(
        script_ready_claims
    )

    display_claim_priority(
        prioritized_claims
    )


if __name__ == "__main__":
    main()
