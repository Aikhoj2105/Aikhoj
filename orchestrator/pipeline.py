"""
AI Khoj — Pipeline Orchestrator v1

Purpose:
Connect AI Khoj agents through a central pipeline.

Current version:
- Basic pipeline structure only
- Existing agents are not modified
"""

from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from orchestrator.adapters.research_adapter import get_latest_research
from orchestrator.adapters import (
    article_extractor_adapter,
    research_analyzer_adapter,
    fact_checker_adapter,
    title_hook_adapter,
    script_writer_adapter,
)


@dataclass
class StageResult:
    stage: str
    status: str
    output_path: Optional[str] = None
    error: Optional[str] = None
    timestamp: str = ""



class AIKhojOrchestrator:
    """Central controller for the AI Khoj pipeline."""

    def __init__(self):
        self.started_at = datetime.now()
        self.results = []
        self.stages = [
            "research",
            "article_extraction",
            "analysis",
            "fact_check",
            "title_hook",
            "script",
        ]

    def record_result(self, stage, status, output_path=None, error=None):
        result = StageResult(
            stage=stage,
            status=status,
            output_path=str(output_path) if output_path else None,
            error=error,
            timestamp=datetime.now().isoformat(),
        )
        self.results.append(result)
        return result

    def run_stage(self, stage, func):
        try:
            output = func()
            output_path = output if isinstance(output, (str, Path)) else None
            return self.record_result(
                stage,
                "success",
                output_path=output_path,
            )
        except Exception as exc:
            return self.record_result(
                stage,
                "failed",
                error=str(exc),
            )

    def snapshot_outputs(self):
        """Capture current pipeline output state without modifying files."""
        output_dirs = {
            "research": Path("outputs/research"),
            "article_extraction": Path("outputs/articles"),
            "analysis": Path("outputs/analysis"),
            "fact_check": Path("outputs/fact_check"),
            "title_hook": Path("outputs/title_hook"),
            "script": Path("outputs/scripts"),
        }

        snapshot = {}

        for stage, directory in output_dirs.items():
            files = []

            if directory.exists():
                for path in directory.iterdir():
                    if path.is_file():
                        stat = path.stat()
                        files.append({
                            "path": str(path),
                            "size": stat.st_size,
                            "mtime": stat.st_mtime,
                        })

            snapshot[stage] = files

        return snapshot

    def dry_run_pipeline(self, stage_functions):
        """Validate pipeline execution without running any stage."""
        print("\n" + "=" * 60)
        print("🧪 AI KHOJ — PIPELINE DRY RUN")
        print("=" * 60)

        planned = []

        for stage in self.stages:
            if stage not in stage_functions:
                raise ValueError(
                    f"No function registered for stage: {stage}"
                )

            func = stage_functions[stage]

            if not callable(func):
                raise TypeError(
                    f"Stage function is not callable: {stage}"
                )

            planned.append(stage)
            print(f"  [DRY] {stage} → {func.__name__}")

        print("=" * 60)
        print("Stages planned:", len(planned))
        print("Execution order:", planned)
        print("⚠️ NO STAGE EXECUTED")
        print("⚠️ NO GEMINI/API CALL")
        print("⚠️ NO FILE MODIFICATION")
        print("=" * 60)

        return planned

    def run_pipeline(self, stage_functions):
        """
        Execute registered pipeline stages sequentially.

        stage_functions:
            Dictionary mapping stage name -> callable.

        Returns:
            List of StageResult objects.

        Behaviour:
            - Runs stages in registered order.
            - Stops immediately when a stage fails.
            - Records success/failure for each executed stage.
            - Does not execute downstream stages after failure.
        """
        self.results = []

        for stage in self.stages:
            if stage not in stage_functions:
                self.record_result(
                    stage,
                    "failed",
                    error=f"No function registered for stage: {stage}",
                )
                break

            func = stage_functions[stage]

            if not callable(func):
                self.record_result(
                    stage,
                    "failed",
                    error=f"Stage function is not callable: {stage}",
                )
                break

            result = self.run_stage(stage, func)

            if result.status != "success":
                break

        return self.results

    def build_stage_functions(self):
        """Build the real adapter mapping for the pipeline."""
        return {
            "research": get_latest_research,

            "article_extraction": (
                lambda: article_extractor_adapter.extract_and_save_from_research(
                    get_latest_research()
                )
            ),

            "analysis": (
                lambda: research_analyzer_adapter.analyze_from_research(
                    get_latest_research()
                )
            ),

            "fact_check": fact_checker_adapter.run_fact_check,

            "title_hook": title_hook_adapter.generate_title_hook,

            "script": script_writer_adapter.generate_script,
        }

    def show_results(self):
        print("\n" + "=" * 60)
        print("📊 AI KHOJ — PIPELINE RESULTS")
        print("=" * 60)

        if not self.results:
            print("No stage results recorded.")
            return

        for result in self.results:
            print(f"Stage  : {result.stage}")
            print(f"Status : {result.status}")
            print(f"Output : {result.output_path or '-'}")
            if result.error:
                print(f"Error  : {result.error}")
            print(f"Time   : {result.timestamp}")
            print("-" * 60)

    def get_research_output(self):
        return get_latest_research()

    def show_pipeline(self):
        print("\n" + "=" * 60)
        print("🤖 AI KHOJ — PIPELINE ORCHESTRATOR v1")
        print("=" * 60)

        for number, stage in enumerate(self.stages, start=1):
            print(f"[{number}/5] {stage}")

        print("=" * 60)


def main():
    orchestrator = AIKhojOrchestrator()
    orchestrator.show_pipeline()


if __name__ == "__main__":
    main()
