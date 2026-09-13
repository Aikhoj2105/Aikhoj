"""
AI Khoj — Script Writer Adapter v1

Purpose:
Provide a stable interface between the orchestrator
and the existing Script Writer v2 agent.
"""

from agents import script_writer_v2


def generate_script():
    """Run the existing Script Writer v2 through the adapter.

    The legacy Script Writer returns None when it stops internally
    because of a failure. Convert that silent failure into an exception
    so the orchestrator can enforce its fail-fast contract.
    """
    result = script_writer_v2.main()

    if result is None:
        raise RuntimeError(
            "Script Writer failed or stopped without producing a result."
        )

    return result
