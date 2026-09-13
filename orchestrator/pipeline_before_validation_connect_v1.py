"""
AI Khoj — Pipeline Orchestrator v1

Purpose:
Connect AI Khoj agents through a central pipeline.

Current version:
- Basic pipeline structure only
- Existing agents are not modified
"""

from datetime import datetime
import json
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

    def validate_artifact(self, stage, output_path):
        """Validate that a stage produced a usable artifact."""

        if output_path is None:
            raise ValueError(
                f"Stage '{stage}' produced no output."
            )

        path = Path(output_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Stage '{stage}' output does not exist: {path}"
            )

        if not path.is_file():
            raise TypeError(
                f"Stage '{stage}' output is not a file: {path}"
            )

        if path.stat().st_size == 0:
            raise ValueError(
                f"Stage '{stage}' output file is empty: {path}"
            )

        return path

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

    def save_run_manifest(self):
        """Save the current pipeline run state as a JSON manifest."""

        manifest_dir = Path("outputs/pipeline_runs")
        manifest_dir.mkdir(parents=True, exist_ok=True)

        run_id = self.started_at.strftime("%Y%m%d_%H%M%S_%f")

        if any(result.status == "failed" for result in self.results):
            pipeline_status = "failed"
        elif len(self.results) == len(self.stages):
            pipeline_status = "success"
        else:
            pipeline_status = "incomplete"

        manifest = {
            "run_id": run_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": datetime.now().isoformat(),
            "status": pipeline_status,
            "stages": [
                {
                    "stage": result.stage,
                    "status": result.status,
                    "output_path": result.output_path,
                    "error": result.error,
                    "timestamp": result.timestamp,
                }
                for result in self.results
            ],
        }

        manifest_path = manifest_dir / f"run_{run_id}.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )

        return manifest_path

    def run_stage(self, stage, func):
        try:
            output = func()

            if output is None:
                raise RuntimeError(
                    f"Stage '{stage}' returned no output."
                )

            if not isinstance(output, (str, Path)):
                raise TypeError(
                    f"Stage '{stage}' returned unsupported output type: "
                    f"{type(output).__name__}"
                )

            output_path = str(output)

            if not Path(output_path).exists():
                raise FileNotFoundError(
                    f"Stage '{stage}' returned a missing output file: "
                    f"{output_path}"
                )

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

        self.save_run_manifest()
        return self.results

    def build_stage_functions(self):
        """Build the real adapter mapping for the pipeline.

        Research is resolved once and its output is reused by
        downstream stages that require the research artifact.
        """

        def run_research():
            self.research_output = get_latest_research()

            if self.research_output is None:
                raise RuntimeError(
                    "Research stage failed to produce an output."
                )

            return self.research_output

        def run_article_extraction():
            if self.research_output is None:
                raise RuntimeError(
                    "Research output is unavailable for Article Extraction."
                )

            self.article_output = (
                article_extractor_adapter
                .extract_and_save_from_research(self.research_output)
            )

            if self.article_output is None:
                raise RuntimeError(
                    "Article Extraction failed to produce an output."
                )

            return self.article_output

        def run_analysis():
            if self.research_output is None:
                raise RuntimeError(
                    "Research output is unavailable for Analysis."
                )

            if self.article_output is None:
                raise RuntimeError(
                    "Article output is unavailable for Analysis."
                )

            return (
                research_analyzer_adapter
                .analyze_from_research(
                    self.research_output,
                    self.article_output,
                )
            )

        return {
            "research": run_research,
            "article_extraction": run_article_extraction,
            "analysis": run_analysis,
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
