from agents import script_writer_v2


def generate_script(
    fact_check_file=None,
    title_hook_file=None,
):
    """Run Script Writer v2 with explicit V2 handoff inputs."""

    result = script_writer_v2.main(
        fact_check_file,
        title_hook_file,
    )

    if result is None:
        raise RuntimeError(
            "Script Writer failed or stopped without producing a result."
        )

    if isinstance(result, dict):
        script_path = result.get("script_path")

        if not script_path:
            raise RuntimeError(
                "Script Writer returned structured output without script_path."
            )

        return script_path

    return result
