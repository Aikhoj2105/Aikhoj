"""
AI Khoj — Title + Hook Adapter v1

Purpose:
Provide a stable interface between the orchestrator
and the existing Title + Hook agent.
"""

from agents import title_hook_agent


def generate_title_hook(research_file=None, fact_check_file=None):
    """Run the existing Title + Hook agent through the adapter.

    The legacy agent uses SystemExit(1) for internal failures.
    Convert that into RuntimeError so the orchestrator can enforce
    its fail-fast stage contract.
    """
    try:
        result = title_hook_agent.main(
            research_file,
            fact_check_file,
        )
    except SystemExit as exc:
        raise RuntimeError(
            f"Title + Hook Agent failed with exit code {exc.code}"
        ) from exc

    if result is None:
        raise RuntimeError(
            "Title + Hook Agent failed or stopped without producing a result."
        )

    return result
