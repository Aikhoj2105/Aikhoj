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

    # --------------------------------------------------------
    # Block 4A — Outline Generator Foundation
    # --------------------------------------------------------

    outline = build_outline_foundation(
        story_plan
    )

    display_outline_foundation(
        outline
    )

    if validate_outline_foundation(
        outline
    ):
        log(
            "✅ Outline foundation validation passed"
        )
    else:
        log(
            "❌ Outline foundation validation failed",
            "ERROR"
        )

    # --------------------------------------------------------
    # Block 4B — AI Outline Generator
    # --------------------------------------------------------

    outline_prompt = build_outline_prompt(
        story_plan
    )

    raw_ai_outline = call_gemini_outline(
        outline_prompt
    )

    ai_outline = parse_ai_outline(
        raw_ai_outline
    )

    display_ai_outline(
        ai_outline
    )

    if validate_ai_outline(
        ai_outline,
        story_plan
    ):
        log(
            "✅ Block 4B AI outline validation passed"
        )
    else:
        log(
            "❌ Block 4B AI outline validation failed",
            "ERROR"
        )

    # --------------------------------------------------------
    # Block 4C — Outline Saver
    # --------------------------------------------------------

    if validate_ai_outline(
        ai_outline,
        story_plan
    ):
        saved_outline_path = save_ai_outline(
            ai_outline
        )

        if saved_outline_path:
            log(
                f"✅ Block 4C outline save passed: "
                f"{saved_outline_path}"
            )
        else:
            log(
                "❌ Block 4C outline save failed",
                "ERROR"
            )

    # --------------------------------------------------------
    # Block 5A — Section Writer Foundation
    # --------------------------------------------------------

    section_writing_tasks = (
        build_section_writing_tasks(
            ai_outline
        )
    )

    display_section_writing_tasks(
        section_writing_tasks
    )

    if validate_section_writing_tasks(
        section_writing_tasks
    ):
        log(
            "✅ Block 5A section writing task validation passed"
        )
    else:
        log(
            "❌ Block 5A section writing task validation failed",
            "ERROR"
        )

    # --------------------------------------------------------
    # Block 5B — AI Section Writer
    # --------------------------------------------------------

    generated_sections = write_script_sections(
        section_writing_tasks
    )

    display_generated_sections(
        generated_sections
    )

    if generated_sections:
        log(
            "✅ Block 5B AI section writing passed"
        )
    else:
        log(
            "❌ Block 5B AI section writing failed",
            "ERROR"
        )

    # --------------------------------------------------------
    # Block 5C — Section Fact-Safety Review
    # --------------------------------------------------------

    reviewed_sections = review_generated_sections(
        generated_sections,
        section_writing_tasks
    )

    display_section_safety_reviews(
        reviewed_sections
    )

    if reviewed_sections:
        log(
            "✅ Block 5C section fact-safety review passed"
        )
    else:
        log(
            "❌ Block 5C section fact-safety review failed",
            "ERROR"
        )


    # --------------------------------------------------------
    # Block 6A — Quality Gate
    # --------------------------------------------------------

    gated_sections = apply_quality_gate(
        reviewed_sections
    )

    display_quality_gate_results(
        gated_sections
    )

    approved_sections = [
        section
        for section in gated_sections
        if section.get("quality_gate_status")
        == QUALITY_GATE_APPROVED
    ]

    held_sections = [
        section
        for section in gated_sections
        if section.get("quality_gate_status")
        == QUALITY_GATE_HOLD
    ]

    log(
        f"Quality Gate approved sections: "
        f"{len(approved_sections)}"
    )

    log(
        f"Quality Gate held sections: "
        f"{len(held_sections)}"
    )

    if gated_sections:
        log(
            "✅ Block 6A Quality Gate passed"
        )
    else:
        log(
            "❌ Block 6A Quality Gate failed",
            "ERROR"
        )




    # --------------------------------------------------------
    # Block 6B — Quality Gate Integrity
    # --------------------------------------------------------

    approved_claim_ids = [
        claim.get("claim_id")
        for claim in script_ready_claims
        if claim.get("claim_id") is not None
    ]

    checked_sections = apply_quality_gate_integrity(
        gated_sections,
        approved_claim_ids
    )

    display_quality_gate_integrity(
        checked_sections
    )

    valid_sections = [
        section
        for section in checked_sections
        if section.get("integrity_status") == "VALID"
    ]

    invalid_sections = [
        section
        for section in checked_sections
        if section.get("integrity_status") == "INVALID"
    ]

    log(
        f"Quality Gate valid sections: "
        f"{len(valid_sections)}"
    )

    log(
        f"Quality Gate invalid sections: "
        f"{len(invalid_sections)}"
    )

    if checked_sections:
        log(
            "✅ Block 6B Quality Gate integrity passed"
        )
    else:
        log(
            "❌ Block 6B Quality Gate integrity failed",
            "ERROR"
        )


    # --------------------------------------------------------
    # Block 6C — Final Quality Gate Decision
    # --------------------------------------------------------

    final_quality_sections = apply_final_quality_gate(
        checked_sections
    )

    display_final_quality_gate(
        final_quality_sections
    )

    final_approved_sections = [
        section
        for section in final_quality_sections
        if section.get("final_quality_status")
        == FINAL_APPROVED
    ]

    final_hold_sections = [
        section
        for section in final_quality_sections
        if section.get("final_quality_status")
        == FINAL_HOLD
    ]

    log(
        f"Final Quality Gate approved sections: "
        f"{len(final_approved_sections)}"
    )

    log(
        f"Final Quality Gate held sections: "
        f"{len(final_hold_sections)}"
    )

    if final_quality_sections:
        log(
            "✅ Block 6C Final Quality Gate passed"
        )
    else:
        log(
            "❌ Block 6C Final Quality Gate failed",
            "ERROR"
        )


# ============================================================
# Block 6A — Quality Gate Foundation
# ============================================================

QUALITY_GATE_APPROVED = "APPROVED"
QUALITY_GATE_HOLD = "HOLD"


def validate_quality_gate_input(reviewed_sections):
    """
    Validate the structure received from Block 5C.

    No Gemini/API call is used.
    """

    if not isinstance(reviewed_sections, list):
        log(
            "Invalid reviewed sections for Quality Gate.",
            "ERROR"
        )
        return False

    if not reviewed_sections:
        log(
            "No reviewed sections available for Quality Gate.",
            "ERROR"
        )
        return False

    for section in reviewed_sections:

        if not isinstance(section, dict):
            log(
                "Invalid section object in Quality Gate input.",
                "ERROR"
            )
            return False

        required_fields = [
            "section_number",
            "claim_ids",
            "narration",
            "safety_status"
        ]

        for field in required_fields:
            if field not in section:
                log(
                    f"Missing Quality Gate field: {field}",
                    "ERROR"
                )
                return False

        if not isinstance(
            section.get("claim_ids"),
            list
        ):
            log(
                "Invalid claim_ids in Quality Gate input.",
                "ERROR"
            )
            return False

        if not isinstance(
            section.get("narration"),
            str
        ):
            log(
                "Invalid narration in Quality Gate input.",
                "ERROR"
            )
            return False

        if not section.get("narration").strip():
            log(
                "Empty narration found in Quality Gate input.",
                "ERROR"
            )
            return False

        if section.get("safety_status") not in [
            "SAFE",
            "REVIEW"
        ]:
            log(
                "Invalid safety status in Quality Gate input.",
                "ERROR"
            )
            return False

    return True


def apply_quality_gate(reviewed_sections):
    """
    Apply deterministic quality rules to safety-reviewed sections.

    SAFE  -> APPROVED
    REVIEW -> HOLD

    No Gemini/API call is used.
    """

    if not validate_quality_gate_input(
        reviewed_sections
    ):
        return []

    gated_sections = []

    for section in reviewed_sections:

        gated_item = dict(section)

        safety_status = section.get(
            "safety_status"
        )

        if safety_status == "SAFE":
            gate_status = QUALITY_GATE_APPROVED
        else:
            gate_status = QUALITY_GATE_HOLD

        gated_item["quality_gate_status"] = gate_status

        gated_sections.append(
            gated_item
        )

    return gated_sections


def display_quality_gate_results(
    gated_sections
):
    """
    Display Quality Gate decisions.
    """

    print()
    print("=" * 60)
    print("QUALITY GATE")
    print("=" * 60)

    if not gated_sections:
        print(
            "No sections available for Quality Gate."
        )
        return

    for section in gated_sections:

        print()

        print(
            f"Section : "
            f"{section['section_number']}"
        )

        print(
            f"Claims  : "
            f"{section['claim_ids']}"
        )

        print(
            f"Safety  : "
            f"{section['safety_status']}"
        )

        print(
            f"Gate    : "
            f"{section['quality_gate_status']}"
        )


# ============================================================
# End of Block 6A
# ============================================================

# ============================================================
# Block 6B — Quality Gate Integrity Checks
# ============================================================

def validate_quality_gate_integrity(gated_sections, approved_claim_ids):
    """
    Validate that approved sections contain only valid claim IDs
    and structurally valid section data.

    No Gemini/API call is used.
    """
    if not isinstance(gated_sections, list):
        log("Invalid gated sections for integrity check.", "ERROR")
        return False

    if not isinstance(approved_claim_ids, list):
        log("Invalid approved claim IDs for integrity check.", "ERROR")
        return False

    approved_claim_ids = set(approved_claim_ids)

    for section in gated_sections:
        if not isinstance(section, dict):
            log("Invalid section object in integrity check.", "ERROR")
            return False

        section_number = section.get("section_number")
        claim_ids = section.get("claim_ids")
        narration = section.get("narration")
        gate_status = section.get("quality_gate_status")

        if not isinstance(section_number, int):
            log("Invalid section number in integrity check.", "ERROR")
            return False

        if not isinstance(claim_ids, list):
            log(
                f"Invalid claim_ids in section {section_number}.",
                "ERROR"
            )
            return False

        if not isinstance(narration, str) or not narration.strip():
            log(
                f"Empty or invalid narration in section {section_number}.",
                "ERROR"
            )
            return False

        if gate_status not in [
            QUALITY_GATE_APPROVED,
            QUALITY_GATE_HOLD
        ]:
            log(
                f"Invalid quality gate status in section {section_number}.",
                "ERROR"
            )
            return False

        for claim_id in claim_ids:
            if claim_id not in approved_claim_ids:
                log(
                    f"Section {section_number} contains invalid "
                    f"claim ID: {claim_id}",
                    "ERROR"
                )
                return False

    return True


def apply_quality_gate_integrity(gated_sections, approved_claim_ids):
    """
    Apply deterministic integrity checks.

    Invalid sections are changed to HOLD.
    No Gemini/API call is used.
    """
    if not isinstance(gated_sections, list):
        return []

    approved_claim_ids = set(approved_claim_ids)

    checked_sections = []

    for section in gated_sections:
        checked_item = dict(section)

        claim_ids = section.get("claim_ids", [])
        narration = section.get("narration", "")
        section_number = section.get("section_number")

        valid_structure = (
            isinstance(section_number, int)
            and isinstance(claim_ids, list)
            and isinstance(narration, str)
            and bool(narration.strip())
        )

        valid_claim_ids = all(
            claim_id in approved_claim_ids
            for claim_id in claim_ids
        )

        if valid_structure and valid_claim_ids:
            checked_item["integrity_status"] = "VALID"
        else:
            checked_item["integrity_status"] = "INVALID"
            checked_item["quality_gate_status"] = QUALITY_GATE_HOLD

        checked_sections.append(checked_item)

    return checked_sections


def display_quality_gate_integrity(checked_sections):
    """
    Display Quality Gate integrity results.
    """
    print()
    print("=" * 60)
    print("QUALITY GATE INTEGRITY")
    print("=" * 60)

    if not checked_sections:
        print("No sections available for integrity check.")
        return

    for section in checked_sections:
        print()
        print(f"Section  : {section['section_number']}")
        print(f"Claims   : {section['claim_ids']}")
        print(f"Integrity: {section['integrity_status']}")
        print(f"Gate     : {section['quality_gate_status']}")

# ============================================================
# End of Block 6B
# ============================================================

# ============================================================
# Block 6C — Final Quality Gate Decision
# ============================================================

FINAL_APPROVED = "FINAL_APPROVED"
FINAL_HOLD = "FINAL_HOLD"


def apply_final_quality_gate(checked_sections):
    """
    Make the final deterministic Quality Gate decision.

    APPROVED + VALID -> FINAL_APPROVED
    Otherwise        -> FINAL_HOLD

    No Gemini/API call is used.
    """
    if not isinstance(checked_sections, list):
        log(
            "Invalid sections for final Quality Gate.",
            "ERROR"
        )
        return []

    final_sections = []

    for section in checked_sections:
        final_item = dict(section)

        quality_status = section.get(
            "quality_gate_status"
        )
        integrity_status = section.get(
            "integrity_status"
        )

        if (
            quality_status == QUALITY_GATE_APPROVED
            and integrity_status == "VALID"
        ):
            final_item["final_quality_status"] = FINAL_APPROVED
        else:
            final_item["final_quality_status"] = FINAL_HOLD

        final_sections.append(final_item)

    return final_sections


def display_final_quality_gate(final_sections):
    """
    Display final Quality Gate decisions.
    """
    print()
    print("=" * 60)
    print("FINAL QUALITY GATE")
    print("=" * 60)

    if not final_sections:
        print("No sections available for final Quality Gate.")
        return

    for section in final_sections:
        print()
        print(f"Section   : {section['section_number']}")
        print(f"Claims    : {section['claim_ids']}")
        print(f"Safety    : {section['quality_gate_status']}")
        print(f"Integrity : {section['integrity_status']}")
        print(f"Final     : {section['final_quality_status']}")


# ============================================================
# End of Block 6C
# ============================================================


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


# ============================================================
# Block 4A — Outline Generator Foundation
# ============================================================

OUTLINE_SECTION_TYPES = {
    "HOOK",
    "BACKGROUND",
    "EVIDENCE",
    "CONCLUSION"
}


def build_outline_foundation(story_plan):
    """
    Convert the story plan into a clean outline structure.

    No Gemini/API call is used.

    Every outline section preserves:
    - section number
    - heading
    - role
    - claim IDs
    - source IDs
    - estimated narration time
    """

    if not story_plan:
        log(
            "No story plan available "
            "for outline generation.",
            "ERROR"
        )
        return []

    outline = []

    for item in story_plan:

        role = item.get("role")

        if role not in OUTLINE_SECTION_TYPES:
            log(
                f"Invalid outline section role: {role}",
                "ERROR"
            )
            return []

        outline_item = {
            "section_number": item.get(
                "section_number"
            ),

            "heading": item.get(
                "heading"
            ),

            "role": role,

            "claim_ids": list(
                item.get(
                    "claim_ids",
                    []
                )
            ),

            "source_ids": list(
                item.get(
                    "source_ids",
                    []
                )
            ),

            "estimated_seconds": item.get(
                "estimated_seconds",
                0
            ),

            "claim": item.get(
                "claim"
            )
        }

        outline.append(
            outline_item
        )

    log(
        f"Outline foundation created: "
        f"{len(outline)} sections"
    )

    return outline


def validate_outline_foundation(outline):
    """
    Validate the outline foundation structure.
    """

    if not isinstance(
        outline,
        list
    ):
        return False

    if not outline:
        return False

    previous_section = 0

    for item in outline:

        if not isinstance(
            item,
            dict
        ):
            return False

        section_number = item.get(
            "section_number"
        )

        if section_number != previous_section + 1:
            return False

        if item.get(
            "role"
        ) not in OUTLINE_SECTION_TYPES:
            return False

        if not item.get(
            "heading"
        ):
            return False

        if not isinstance(
            item.get("claim_ids"),
            list
        ):
            return False

        if not item.get(
            "claim_ids"
        ):
            return False

        if not isinstance(
            item.get("source_ids"),
            list
        ):
            return False

        if not isinstance(
            item.get("estimated_seconds"),
            int
        ):
            return False

        if item.get(
            "estimated_seconds"
        ) <= 0:
            return False

        if not item.get(
            "claim"
        ):
            return False

        previous_section = section_number

    return True


def display_outline_foundation(outline):
    """
    Display the generated outline foundation.
    """

    print()
    print("=" * 60)
    print("OUTLINE FOUNDATION")
    print("=" * 60)

    if not outline:
        print("No outline available.")
        return

    for item in outline:

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
            f"Claims   : "
            f"{item['claim_ids']}"
        )

        print(
            f"Sources  : "
            f"{item['source_ids']}"
        )

        print(
            f"Duration : "
            f"{item['estimated_seconds']} sec"
        )

        print(
            f"Claim    : "
            f"{item['claim']}"
        )



# ============================================================
# Block 4B — AI Outline Generator
# ============================================================

import json
import os
import urllib.request
import urllib.error


GEMINI_MODEL = "gemini-3.5-flash"


def build_outline_prompt(story_plan):
    """
    Build a strict Gemini prompt for outline generation.

    Gemini must:
    - Use only approved claims.
    - Not introduce new factual claims.
    - Preserve claim IDs.
    - Return valid JSON only.
    """

    claims_payload = []

    for item in story_plan:
        claims_payload.append({
            "section_number": item.get(
                "section_number"
            ),
            "role": item.get(
                "role"
            ),
            "heading": item.get(
                "heading"
            ),
            "claim_id": item.get(
                "claim_id"
            ),
            "claim": item.get(
                "claim"
            ),
            "source_ids": item.get(
                "source_ids",
                []
            ),
            "estimated_seconds": item.get(
                "estimated_seconds",
                0
            )
        })

    claims_json = json.dumps(
        claims_payload,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
You are the outline planning engine for a Hindi/Hinglish
faceless YouTube channel called AI Khoj.

Create a detailed YouTube video outline using ONLY the
approved claims provided below.

STRICT RULES:

1. Do NOT create new factual claims.
2. Do NOT add statistics, dates, names, examples, or facts
   that are not present in the approved claims.
3. Preserve every claim_id exactly.
4. Every outline section must reference one or more
   approved claim IDs.
5. Keep the narrative logical and engaging.
6. The outline is for a documentary/educational YouTube
   video.
7. Return ONLY valid JSON.
8. Do not use Markdown.
9. Do not add commentary outside JSON.

APPROVED STORY PLAN:

{claims_json}

Return JSON using exactly this structure:

{{
  "title_direction": "string",
  "sections": [
    {{
      "section_number": 1,
      "heading": "string",
      "role": "HOOK",
      "claim_ids": [1],
      "purpose": "string",
      "key_points": [
        "string"
      ],
      "estimated_seconds": 20
    }}
  ]
}}
"""

    return prompt


def call_gemini_outline(prompt):
    """
    Send the outline-generation prompt to Gemini.
    """

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:
        log(
            "GEMINI_API_KEY not found.",
            "ERROR"
        )
        return None

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
        f"?key={api_key}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json"
        }
    }

    data = json.dumps(
        payload
    ).encode(
        "utf-8"
    )

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            response_data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

        text = (
            response_data
            ["candidates"][0]
            ["content"]["parts"][0]
            ["text"]
        )

        return text

    except urllib.error.HTTPError as error:

        log(
            f"Gemini HTTP error: "
            f"{error.code}",
            "ERROR"
        )

        try:
            error_body = (
                error.read()
                .decode("utf-8")
            )

            print(error_body)

        except Exception:
            pass

        return None

    except Exception as error:

        log(
            f"Gemini request failed: "
            f"{error}",
            "ERROR"
        )

        return None


def parse_ai_outline(raw_text):
    """
    Parse Gemini's JSON outline.
    """

    if not raw_text:
        return None

    try:

        outline = json.loads(
            raw_text
        )

        if not isinstance(
            outline,
            dict
        ):
            return None

        if not isinstance(
            outline.get("sections"),
            list
        ):
            return None

        return outline

    except json.JSONDecodeError as error:

        log(
            f"Invalid Gemini JSON: "
            f"{error}",
            "ERROR"
        )

        return None


def validate_ai_outline(
    outline,
    story_plan
):
    """
    Safety validation for the AI-generated outline.

    The outline may reorganize wording, but it cannot
    reference claim IDs that were not approved.
    """

    if not isinstance(
        outline,
        dict
    ):
        return False

    sections = outline.get(
        "sections"
    )

    if not isinstance(
        sections,
        list
    ):
        return False

    if not sections:
        return False

    approved_claim_ids = {
        item.get("claim_id")
        for item in story_plan
        if item.get("claim_id") is not None
    }

    valid_roles = {
        "HOOK",
        "BACKGROUND",
        "EVIDENCE",
        "CONCLUSION"
    }

    previous_section = 0

    for section in sections:

        if not isinstance(
            section,
            dict
        ):
            return False

        section_number = section.get(
            "section_number"
        )

        if section_number != (
            previous_section + 1
        ):
            return False

        if section.get(
            "role"
        ) not in valid_roles:
            return False

        claim_ids = section.get(
            "claim_ids"
        )

        if not isinstance(
            claim_ids,
            list
        ):
            return False

        if not claim_ids:
            return False

        for claim_id in claim_ids:

            if claim_id not in (
                approved_claim_ids
            ):
                return False

        if not section.get(
            "heading"
        ):
            return False

        if not section.get(
            "purpose"
        ):
            return False

        if not isinstance(
            section.get("key_points"),
            list
        ):
            return False

        if not isinstance(
            section.get(
                "estimated_seconds"
            ),
            int
        ):
            return False

        if section.get(
            "estimated_seconds"
        ) <= 0:
            return False

        previous_section = (
            section_number
        )

    return True


def display_ai_outline(outline):
    """
    Display the AI-generated outline.
    """

    print()
    print("=" * 60)
    print("AI-GENERATED OUTLINE")
    print("=" * 60)

    if not outline:
        print("No AI outline available.")
        return

    print()
    print(
        f"Title Direction: "
        f"{outline.get('title_direction', '')}"
    )

    for section in outline.get(
        "sections",
        []
    ):

        print()
        print(
            f"Section : "
            f"{section['section_number']}"
        )

        print(
            f"Heading : "
            f"{section['heading']}"
        )

        print(
            f"Role    : "
            f"{section['role']}"
        )

        print(
            f"Claims  : "
            f"{section['claim_ids']}"
        )

        print(
            f"Purpose : "
            f"{section['purpose']}"
        )

        print(
            f"Duration: "
            f"{section['estimated_seconds']} sec"
        )

        print("Key Points:")

        for point in section.get(
            "key_points",
            []
        ):

            print(
                f"  - {point}"
            )


# ============================================================
# End of Block 4B
# ============================================================


# ============================================================
# Block 4C — Outline Saver
# ============================================================

def save_ai_outline(outline):
    """
    Save the validated AI-generated outline as JSON.

    Returns:
        Path of the saved file, or None on failure.
    """

    if not isinstance(outline, dict):
        log(
            "Cannot save invalid AI outline.",
            "ERROR"
        )
        return None

    sections = outline.get("sections")

    if not isinstance(sections, list):
        log(
            "Cannot save outline without sections.",
            "ERROR"
        )
        return None

    SCRIPT_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = current_timestamp()

    output_path = (
        SCRIPT_OUTPUT_DIR
        / f"outline_{timestamp.replace('-', '').replace(' ', '_').replace(':', '')}.json"
    )

    try:
        output_path.write_text(
            json.dumps(
                outline,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        log(
            f"AI outline saved: {output_path}"
        )

        return output_path

    except Exception as error:

        log(
            f"Failed to save AI outline: {error}",
            "ERROR"
        )

        return None


def load_ai_outline(path):
    """
    Load a previously saved AI outline.
    """

    if not path:
        return None

    try:

        outline = json.loads(
            Path(path).read_text(
                encoding="utf-8"
            )
        )

        return outline

    except Exception as error:

        log(
            f"Failed to load AI outline: {error}",
            "ERROR"
        )

        return None


# ============================================================
# End of Block 4C
# ============================================================



# ============================================================
# Block 5A — Section Writer Foundation
# ============================================================

def build_section_writing_tasks(ai_outline):
    """
    Convert the validated AI outline into section-writing tasks.

    No Gemini/API call is used.

    Every task preserves:
    - section number
    - heading
    - role
    - claim IDs
    - estimated narration time
    - purpose
    - key points
    """

    if not isinstance(
        ai_outline,
        dict
    ):
        log(
            "Invalid AI outline for section writing.",
            "ERROR"
        )
        return []

    sections = ai_outline.get(
        "sections"
    )

    if not isinstance(
        sections,
        list
    ):
        log(
            "AI outline contains no valid sections.",
            "ERROR"
        )
        return []

    writing_tasks = []

    for section in sections:

        if not isinstance(
            section,
            dict
        ):
            log(
                "Invalid section found in AI outline.",
                "ERROR"
            )
            return []

        section_number = section.get(
            "section_number"
        )

        heading = section.get(
            "heading"
        )

        role = section.get(
            "role"
        )

        claim_ids = section.get(
            "claim_ids",
            []
        )

        purpose = section.get(
            "purpose"
        )

        key_points = section.get(
            "key_points",
            []
        )

        estimated_seconds = section.get(
            "estimated_seconds",
            0
        )

        if section_number is None:
            return []

        if not heading:
            return []

        if not role:
            return []

        if not isinstance(
            claim_ids,
            list
        ) or not claim_ids:
            return []

        if not purpose:
            return []

        if not isinstance(
            key_points,
            list
        ):
            return []

        if not isinstance(
            estimated_seconds,
            int
        ) or estimated_seconds <= 0:
            return []

        task = {
            "section_number": section_number,
            "heading": heading,
            "role": role,
            "claim_ids": list(
                claim_ids
            ),
            "purpose": purpose,
            "key_points": list(
                key_points
            ),
            "estimated_seconds": (
                estimated_seconds
            )
        }

        writing_tasks.append(
            task
        )

    log(
        f"Section writing tasks created: "
        f"{len(writing_tasks)}"
    )

    return writing_tasks


def validate_section_writing_tasks(
    writing_tasks
):
    """
    Validate section-writing task structure.
    """

    if not isinstance(
        writing_tasks,
        list
    ):
        return False

    if not writing_tasks:
        return False

    previous_section = 0

    for task in writing_tasks:

        if not isinstance(
            task,
            dict
        ):
            return False

        section_number = task.get(
            "section_number"
        )

        if section_number != (
            previous_section + 1
        ):
            return False

        if not task.get(
            "heading"
        ):
            return False

        if not task.get(
            "role"
        ):
            return False

        claim_ids = task.get(
            "claim_ids"
        )

        if not isinstance(
            claim_ids,
            list
        ):
            return False

        if not claim_ids:
            return False

        if not task.get(
            "purpose"
        ):
            return False

        if not isinstance(
            task.get("key_points"),
            list
        ):
            return False

        if not isinstance(
            task.get(
                "estimated_seconds"
            ),
            int
        ):
            return False

        if task.get(
            "estimated_seconds"
        ) <= 0:
            return False

        previous_section = (
            section_number
        )

    return True


def display_section_writing_tasks(
    writing_tasks
):
    """
    Display section-writing tasks.
    """

    print()
    print("=" * 60)
    print("SECTION WRITING TASKS")
    print("=" * 60)

    if not writing_tasks:
        print(
            "No section writing tasks available."
        )
        return

    for task in writing_tasks:

        print()

        print(
            f"Section  : "
            f"{task['section_number']}"
        )

        print(
            f"Heading  : "
            f"{task['heading']}"
        )

        print(
            f"Role     : "
            f"{task['role']}"
        )

        print(
            f"Claims   : "
            f"{task['claim_ids']}"
        )

        print(
            f"Purpose  : "
            f"{task['purpose']}"
        )

        print(
            f"Duration : "
            f"{task['estimated_seconds']} sec"
        )

        print("Key Points:")

        for point in task.get(
            "key_points",
            []
        ):

            print(
                f"  - {point}"
            )


# ============================================================
# End of Block 5A
# ============================================================


# ============================================================
# Block 5B — AI Section Writer
# ============================================================

def build_section_writer_prompt(task):
    """
    Build a controlled Gemini prompt for writing one section.

    The writer must stay strictly within the approved
    section task and its claim IDs.
    """

    task_json = json.dumps(
        task,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
You are the section-writing engine for a Hindi/Hinglish
faceless YouTube channel called AI Khoj.

Write ONLY the narration for the approved section below.

STRICT RULES:

1. Use ONLY the information present in the provided task.
2. Do NOT invent facts, statistics, dates, names, examples,
   technical specifications, or claims.
3. Do NOT introduce any new factual claim.
4. Preserve every claim ID exactly.
5. The narration must support the listed claim IDs.
6. Do NOT include citation markers, source numbers, reference markers, or bracketed IDs such as [1], [2], etc. inside the narration. Do NOT write source references such as "Source 1" or "(1)". Claim IDs must remain only in the JSON claim_ids field.
7. Follow the provided purpose and key points.
8. Write in natural Hindi/Hinglish.
9. Use a documentary/educational storytelling tone.
10. Make the narration engaging but fact-safe.
11. Do not mention these instructions.
12. Do not use Markdown headings.
13. Return ONLY valid JSON.
14. Do not add commentary outside JSON.

APPROVED SECTION TASK:

{task_json}

Return JSON using exactly this structure:

{{
  "section_number": {task.get("section_number")},
  "heading": "{task.get("heading")}",
  "role": "{task.get("role")}",
  "claim_ids": {json.dumps(task.get("claim_ids", []))},
  "estimated_seconds": {task.get("estimated_seconds", 0)},
  "narration": "string"
}}
"""

    return prompt


def call_gemini_section_writer(prompt):
    """
    Send one section-writing request to Gemini.

    One Gemini call = one section.
    """

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:
        log(
            "GEMINI_API_KEY not found.",
            "ERROR"
        )
        return None

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
        f"?key={api_key}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "responseMimeType": "application/json"
        }
    }

    data = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            response_data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

        text = (
            response_data["candidates"][0]
            ["content"]["parts"][0]["text"]
        )

        return text

    except urllib.error.HTTPError as error:

        log(
            f"Gemini HTTP error: {error.code}",
            "ERROR"
        )

        try:
            error_body = (
                error.read()
                .decode("utf-8")
            )

            print(error_body)

        except Exception:
            pass

        return None

    except Exception as error:

        log(
            f"Gemini section writer failed: {error}",
            "ERROR"
        )

        return None


def parse_section_writer_output(raw_text):
    """
    Parse Gemini section JSON.
    """

    if not raw_text:
        return None

    try:

        result = json.loads(
            raw_text
        )

        if not isinstance(
            result,
            dict
        ):
            return None

        return result

    except json.JSONDecodeError as error:

        log(
            f"Invalid section writer JSON: {error}",
            "ERROR"
        )

        return None


def validate_section_writer_output(
    result,
    task
):
    """
    Validate generated narration against
    the original section-writing task.
    """

    if not isinstance(
        result,
        dict
    ):
        return False

    if result.get(
        "section_number"
    ) != task.get(
        "section_number"
    ):
        return False

    if result.get(
        "heading"
    ) != task.get(
        "heading"
    ):
        return False

    if result.get(
        "role"
    ) != task.get(
        "role"
    ):
        return False

    if result.get(
        "claim_ids"
    ) != task.get(
        "claim_ids"
    ):
        return False

    if result.get(
        "estimated_seconds"
    ) != task.get(
        "estimated_seconds"
    ):
        return False

    narration = result.get(
        "narration"
    )

    if not isinstance(
        narration,
        str
    ):
        return False

    if not narration.strip():
        return False

    return True


def write_script_sections(
    writing_tasks
):
    """
    Generate narration for every approved section.

    Each section gets its own Gemini call.
    """

    if not isinstance(
        writing_tasks,
        list
    ):
        log(
            "Invalid writing tasks.",
            "ERROR"
        )
        return []

    if not writing_tasks:
        log(
            "No writing tasks available.",
            "ERROR"
        )
        return []

    generated_sections = []

    for task in writing_tasks:

        log(
            f"Writing section "
            f"{task.get('section_number')}..."
        )

        prompt = build_section_writer_prompt(
            task
        )

        raw_result = call_gemini_section_writer(
            prompt
        )

        result = parse_section_writer_output(
            raw_result
        )

        if not validate_section_writer_output(
            result,
            task
        ):
            log(
                f"Section "
                f"{task.get('section_number')} "
                f"failed validation.",
                "ERROR"
            )
            return []

        generated_sections.append(
            result
        )

        log(
            f"Section "
            f"{task.get('section_number')} "
            f"generated successfully."
        )

    log(
        f"Generated sections: "
        f"{len(generated_sections)}"
    )

    return generated_sections


def display_generated_sections(
    generated_sections
):
    """
    Display generated narration sections.
    """

    print()
    print("=" * 60)
    print("AI-GENERATED SCRIPT SECTIONS")
    print("=" * 60)

    if not generated_sections:
        print(
            "No generated sections available."
        )
        return

    for section in generated_sections:

        print()

        print(
            f"Section  : "
            f"{section['section_number']}"
        )

        print(
            f"Heading  : "
            f"{section['heading']}"
        )

        print(
            f"Role     : "
            f"{section['role']}"
        )

        print(
            f"Claims   : "
            f"{section['claim_ids']}"
        )

        print(
            f"Duration : "
            f"{section['estimated_seconds']} sec"
        )

        print("Narration:")

        print(
            section["narration"]
        )


# ============================================================
# End of Block 5B
# ============================================================


# ============================================================
# Block 5C — Section Fact-Safety Review
# ============================================================

def build_section_safety_prompt(
    generated_section,
    writing_task
):
    """
    Build a Gemini prompt to review generated narration
    against the approved section task.
    """

    review_payload = {
        "approved_task": writing_task,
        "generated_section": generated_section
    }

    review_json = json.dumps(
        review_payload,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
You are the fact-safety reviewer for the Hindi/Hinglish
YouTube channel AI Khoj.

Review the generated narration against the approved
section task.

STRICT RULES:

1. Check whether the narration stays within the approved
   claims and key points.
2. Identify any new factual claim introduced by the writer.
3. Do NOT judge writing style.
4. Do NOT rewrite the narration.
5. Do NOT add new facts.
6. Claim IDs must remain unchanged.
7. If the narration contains only information supported by
   the approved task, mark it SAFE.
8. If the narration introduces unsupported factual content,
   mark it REVIEW.
9. Return ONLY valid JSON.
10. Do not use Markdown.
11. Do not add commentary outside JSON.

REVIEW DATA:

{review_json}

Return JSON using exactly this structure:

{{
  "section_number": {generated_section.get("section_number")},
  "claim_ids": {json.dumps(generated_section.get("claim_ids", []))},
  "status": "SAFE",
  "issues": [],
  "reason": "string"
}}
"""

    return prompt


def call_gemini_section_safety_review(
    prompt
):
    """
    Send one section to Gemini for fact-safety review.
    """

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:
        log(
            "GEMINI_API_KEY not found.",
            "ERROR"
        )
        return None

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
        f"?key={api_key}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json"
        }
    }

    data = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            response_data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

        text = (
            response_data["candidates"][0]
            ["content"]["parts"][0]["text"]
        )

        return text

    except urllib.error.HTTPError as error:

        log(
            f"Gemini safety review HTTP error: "
            f"{error.code}",
            "ERROR"
        )

        try:

            error_body = (
                error.read()
                .decode("utf-8")
            )

            print(error_body)

        except Exception:
            pass

        return None

    except Exception as error:

        log(
            f"Gemini safety review failed: {error}",
            "ERROR"
        )

        return None


def parse_section_safety_review(
    raw_text
):
    """
    Parse Gemini safety review JSON.
    """

    if not raw_text:
        return None

    try:

        result = json.loads(
            raw_text
        )

        if not isinstance(
            result,
            dict
        ):
            return None

        return result

    except json.JSONDecodeError as error:

        log(
            f"Invalid safety review JSON: {error}",
            "ERROR"
        )

        return None


def validate_section_safety_review(
    review,
    generated_section
):
    """
    Validate the structure of the safety review.
    """

    if not isinstance(
        review,
        dict
    ):
        return False

    if review.get(
        "section_number"
    ) != generated_section.get(
        "section_number"
    ):
        return False

    if review.get(
        "claim_ids"
    ) != generated_section.get(
        "claim_ids"
    ):
        return False

    if review.get(
        "status"
    ) not in {
        "SAFE",
        "REVIEW"
    }:
        return False

    if not isinstance(
        review.get("issues"),
        list
    ):
        return False

    if not isinstance(
        review.get("reason"),
        str
    ):
        return False

    if not review.get(
        "reason"
    ).strip():
        return False

    return True


def review_generated_sections(
    generated_sections,
    writing_tasks
):
    """
    Review every generated section for factual safety.
    """

    if not isinstance(
        generated_sections,
        list
    ):
        log(
            "Invalid generated sections.",
            "ERROR"
        )
        return []

    if not isinstance(
        writing_tasks,
        list
    ):
        log(
            "Invalid writing tasks.",
            "ERROR"
        )
        return []

    if len(
        generated_sections
    ) != len(
        writing_tasks
    ):
        log(
            "Generated sections and writing tasks "
            "count mismatch.",
            "ERROR"
        )
        return []

    reviewed_sections = []

    for generated_section, task in zip(
        generated_sections,
        writing_tasks
    ):

        log(
            f"Reviewing section "
            f"{generated_section.get('section_number')}..."
        )

        prompt = build_section_safety_prompt(
            generated_section,
            task
        )

        raw_review = (
            call_gemini_section_safety_review(
                prompt
            )
        )

        review = parse_section_safety_review(
            raw_review
        )

        if not validate_section_safety_review(
            review,
            generated_section
        ):
            log(
                f"Section "
                f"{generated_section.get('section_number')} "
                f"safety review validation failed.",
                "ERROR"
            )
            return []

        reviewed_item = dict(
            generated_section
        )

        reviewed_item["safety_status"] = (
            review["status"]
        )

        reviewed_item["safety_issues"] = (
            review["issues"]
        )

        reviewed_item["safety_reason"] = (
            review["reason"]
        )

        reviewed_sections.append(
            reviewed_item
        )

        log(
            f"Section "
            f"{generated_section.get('section_number')} "
            f"safety status: "
            f"{review['status']}"
        )

    log(
        f"Safety-reviewed sections: "
        f"{len(reviewed_sections)}"
    )

    return reviewed_sections


def display_section_safety_reviews(
    reviewed_sections
):
    """
    Display safety review results.
    """

    print()
    print("=" * 60)
    print("SECTION FACT-SAFETY REVIEW")
    print("=" * 60)

    if not reviewed_sections:
        print(
            "No reviewed sections available."
        )
        return

    for section in reviewed_sections:

        print()

        print(
            f"Section : "
            f"{section['section_number']}"
        )

        print(
            f"Claims  : "
            f"{section['claim_ids']}"
        )

        print(
            f"Status  : "
            f"{section['safety_status']}"
        )

        print(
            f"Reason  : "
            f"{section['safety_reason']}"
        )

        issues = section.get(
            "safety_issues",
            []
        )

        if issues:

            print("Issues:")

            for issue in issues:

                print(
                    f"  - {issue}"
                )


# ============================================================
# End of Block 5C
# ============================================================

if __name__ == "__main__":
    main()
