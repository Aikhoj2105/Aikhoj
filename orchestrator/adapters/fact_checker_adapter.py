"""
AI Khoj — Fact Checker Adapter v1

Purpose:
Provide a stable interface between the orchestrator
and the existing Fact Checker agent.
"""

from agents import fact_checker_v3


def run_fact_check(research_file=None):
    """Run the existing Fact Checker through the adapter.

    The legacy Fact Checker returns None when it stops internally because
    of an error or missing input. The orchestrator uses exceptions as the
    failure contract, so convert that silent failure into an exception.
    """
    result = fact_checker_v3.main(research_file)

    if result is None:
        raise RuntimeError(
            "Fact Checker failed or stopped without producing a result."
        )

    return result
