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


# ============================================================
# Block 3B — Narrative Planner
# ============================================================

NARRATIVE_ROLES = {
    "HOOK": 20,
    "BACKGROUND": 30,
    "EVIDENCE": 45,
    "CONCLUSION": 20
}


def build_narrative_plan(prioritized_claims):
    """
    Convert prioritized claims into a deterministic
    narrative structure.

    No Gemini/API call is used.

    Rules:
    - Highest-priority claim becomes the HOOK.
    - The next suitable claim becomes BACKGROUND.
    - Middle claims become EVIDENCE.
    - The final suitable claim becomes CONCLUSION.
    """

    if not prioritized_claims:
        log(
            "No prioritized claims available "
            "for narrative planning.",
            "ERROR"
        )
        return []

    claims = [
        dict(item)
        for item in prioritized_claims
        if item.get("claim_id") is not None
        and item.get("claim")
    ]

    if not claims:
        log(
            "No valid claims available "
            "for narrative planning.",
            "ERROR"
        )
        return []

    plan = []

    total = len(claims)

    for index, claim in enumerate(claims):

        if index == 0:
            role = "HOOK"

        elif total == 2 and index == 1:
            role = "CONCLUSION"

        elif index == 1:
            role = "BACKGROUND"

        elif index == total - 1:
            role = "CONCLUSION"

        else:
            role = "EVIDENCE"

        estimated_seconds = NARRATIVE_ROLES[
            role
        ]

        plan_item = {
            "claim_id": claim["claim_id"],
            "claim": claim["claim"],
            "priority": claim.get(
                "priority",
                "UNKNOWN"
            ),
            "priority_score": claim.get(
                "priority_score",
                0
            ),
            "role": role,
            "estimated_seconds": estimated_seconds,
            "source_ids": claim.get(
                "source_ids",
                []
            )
        }

        plan.append(plan_item)

    log(
        f"Narrative plan created: "
        f"{len(plan)} sections"
    )

    return plan


def validate_narrative_plan(narrative_plan):
    """
    Validate the structure of the narrative plan.
    """

    if not isinstance(
        narrative_plan,
        list
    ):
        return False

    if not narrative_plan:
        return False

    valid_roles = {
        "HOOK",
        "BACKGROUND",
        "EVIDENCE",
        "CONCLUSION"
    }

    for item in narrative_plan:

        if not isinstance(
            item,
            dict
        ):
            return False

        if item.get("claim_id") is None:
            return False

        if not item.get("claim"):
            return False

        if item.get("role") not in valid_roles:
            return False

        if not isinstance(
            item.get("estimated_seconds"),
            int
        ):
            return False

        if item.get("estimated_seconds") <= 0:
            return False

    return True


def display_narrative_plan(narrative_plan):
    """
    Display the narrative plan in a compact format.
    """

    print()
    print("=" * 60)
    print("NARRATIVE PLAN")
    print("=" * 60)

    if not narrative_plan:
        print("No narrative plan available.")
        return

    for item in narrative_plan:

        print()

        print(
            f"Claim {item['claim_id']}"
        )

        print(
            f"Role     : "
            f"{item['role']}"
        )

        print(
            f"Priority : "
            f"{item['priority']}"
        )

        print(
            f"Score    : "
            f"{item['priority_score']}"
        )

        print(
            f"Duration : "
            f"{item['estimated_seconds']} sec"
        )

        print(
            f"Sources  : "
            f"{item['source_ids']}"
        )

        print(
            f"Claim    : "
            f"{item['claim']}"
        )

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

    # --------------------------------------------------------
    # Block 3B — Narrative Planner
    # --------------------------------------------------------

    narrative_plan = build_narrative_plan(
        prioritized_claims
    )

    display_narrative_plan(
        narrative_plan
    )

    if validate_narrative_plan(
        narrative_plan
    ):
        log(
            "✅ Narrative plan validation passed"
        )
    else:
        log(
            "❌ Narrative plan validation failed",
            "ERROR"
        )

    # --------------------------------------------------------
    # Block 3C — Story Plan Builder
    # --------------------------------------------------------

    story_plan = build_story_plan(
        narrative_plan
    )

    display_story_plan(
        story_plan
    )

    if validate_story_plan(
        story_plan
    ):
        log(
            "✅ Story plan validation passed"
        )
    else:
        log(
            "❌ Story plan validation failed",
            "ERROR"
        )




# ============================================================
# Block 3C — Story Plan Builder
# ============================================================

STORY_SECTION_ORDER = {
    "HOOK": 1,
    "BACKGROUND": 2,
    "EVIDENCE": 3,
    "CONCLUSION": 4
}


def build_story_plan(narrative_plan):
    """
    Convert the narrative plan into a structured story blueprint.

    No Gemini/API call is used.

    Each story section keeps:
    - claim_id
    - claim
    - narrative role
    - priority
    - source IDs
    - estimated narration time
    - traceability information
    """

    if not narrative_plan:
        log(
            "No narrative plan available "
            "for story plan building.",
            "ERROR"
        )
        return []

    story_plan = []

    for item in narrative_plan:

        role = item.get(
            "role",
            "UNKNOWN"
        )

        if role not in STORY_SECTION_ORDER:
            log(
                f"Invalid narrative role: {role}",
                "ERROR"
            )
            return []

        story_item = {
            "section_number": len(
                story_plan
            ) + 1,

            "heading": role.title(),

            "role": role,

            "claim_id": item.get(
                "claim_id"
            ),

            "claim": item.get(
                "claim"
            ),

            "priority": item.get(
                "priority",
                "UNKNOWN"
            ),

            "priority_score": item.get(
                "priority_score",
                0
            ),

            "estimated_seconds": item.get(
                "estimated_seconds",
                0
            ),

            "source_ids": item.get(
                "source_ids",
                []
            ),

            # Internal traceability
            "claim_ids": [
                item.get("claim_id")
            ]
        }

        story_plan.append(
            story_item
        )

    log(
        f"Story plan created: "
        f"{len(story_plan)} sections"
    )

    return story_plan


def validate_story_plan(story_plan):
    """
    Validate the generated story blueprint.
    """

    if not isinstance(
        story_plan,
        list
    ):
        return False

    if not story_plan:
        return False

    required_roles = {
        "HOOK",
        "BACKGROUND",
        "EVIDENCE",
        "CONCLUSION"
    }

    previous_section_number = 0

    for item in story_plan:

        if not isinstance(
            item,
            dict
        ):
            return False

        if item.get(
            "section_number"
        ) != previous_section_number + 1:
            return False

        if item.get(
            "role"
        ) not in required_roles:
            return False

        if item.get(
            "claim_id"
        ) is None:
            return False

        if not item.get(
            "claim"
        ):
            return False

        if not isinstance(
            item.get(
                "estimated_seconds"
            ),
            int
        ):
            return False

        if item.get(
            "estimated_seconds"
        ) <= 0:
            return False

        if not isinstance(
            item.get(
                "claim_ids"
            ),
            list
        ):
            return False

        if item.get(
            "claim_id"
        ) not in item.get(
            "claim_ids"
        ):
            return False

        previous_section_number = item[
            "section_number"
        ]

    return True


def display_story_plan(story_plan):
    """
    Display the structured story blueprint.
    """

    print()
    print("=" * 60)
    print("STORY PLAN")
    print("=" * 60)

    if not story_plan:
        print("No story plan available.")
        return

    for item in story_plan:

        print()

        print(
            f"Section  : "
            f"{item['section_number']}"
        )

        print(
            f"Heading  : "
            f"{item['heading']}"
        )

        print(
            f"Role     : "
            f"{item['role']}"
        )

        print(
            f"Claim ID : "
            f"{item['claim_id']}"
        )

        print(
            f"Priority : "
            f"{item['priority']}"
        )

        print(
            f"Duration : "
            f"{item['estimated_seconds']} sec"
        )

        print(
            f"Sources  : "
            f"{item['source_ids']}"
        )

        print(
            f"Trace    : "
            f"{item['claim_ids']}"
        )

        print(
            f"Claim    : "
            f"{item['claim']}"
        )

if __name__ == "__main__":
    main()
