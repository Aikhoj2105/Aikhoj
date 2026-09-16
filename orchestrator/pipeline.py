"""
AI Khoj — Pipeline Orchestrator v1

Purpose:
Connect AI Khoj agents through a central pipeline.

Current version:
- Basic pipeline structure only
- Existing agents are not modified
"""

from datetime import datetime
import sys
import json
import re
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
from core.content_package_builder import build_content_package
from core.content_package_validator import validate_content_package


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

        # Explicit artifact handoff state
        self.research_output = None
        self.article_output = None
        self.analysis_output = None
        self.fact_check_output = None
        self.title_hook_output = None
        self.script_output = None
        self.content_package_output = None

        self.stages = [
            "research",
            "article_extraction",
            "analysis",
            "fact_check",
            "title_hook",
            "script",
            "content_package",
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

            validated_path = self.validate_artifact(
                stage,
                output_path,
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

            if stage == "content_package":
                result = self.run_content_package_stage()
            else:
                result = self.run_stage(stage, func)
            if result.status != "success":
                break

        self.save_run_manifest()
        return self.results

    def run_content_package_stage(self):
        """Run the Content Package stage and record its directory output."""

        try:
            output = self.run_content_package()

            if output is None:
                raise RuntimeError("Content Package stage returned no output.")

            output_path = Path(output)

            if not output_path.is_dir():
                raise TypeError(
                    "Content Package output must be a directory: "
                    f"{output_path}"
                )

            return self.record_result(
                "content_package",
                "success",
                output_path=output_path,
            )

        except Exception as exc:
            return self.record_result(
                "content_package",
                "failed",
                error=str(exc),
            )

    def extract_content_metadata(self, research_file):
        """Extract deterministic package metadata from research output."""

        research_path = Path(research_file)

        if not research_path.is_file():
            raise FileNotFoundError(
                f"Research file not found: {research_path}"
            )

        text = research_path.read_text(encoding="utf-8")

        source_match = re.search(
            r"^\*\*Source:\*\*\s*(https?://\S+)",
            text,
            re.MULTILINE,
        )

        if not source_match:
            raise ValueError(
                "Source URL not found in research report."
            )

        source_url = source_match.group(1).strip()

        program_match = re.search(
            r"\*\s*\*\*Program Name:\*\*\s*([^\n]+)",
            text,
        )

        if program_match:
            topic_title = program_match.group(1).strip()
            topic_title = topic_title.split(" (", 1)[0].strip()
        else:
            topic_title = "AI Khoj Topic"

        return {
            "topic_title": topic_title,
            "source_url": source_url,
            "category": "ai",
        }

    def run_content_package(self):
        """Build and validate the final Content Package."""

        required_outputs = {
            "research": self.research_output,
            "article": self.article_output,
            "analysis": self.analysis_output,
            "fact_check": self.fact_check_output,
            "title_hook": self.title_hook_output,
            "script": self.script_output,
        }

        for name, output in required_outputs.items():
            if output is None:
                raise RuntimeError(
                    f"{name.replace('_', ' ').title()} output is "
                    "unavailable for Content Package."
                )

        metadata = self.extract_content_metadata(
            self.research_output
        )

        package_dir = build_content_package(
            research_file=self.research_output,
            article_file=self.article_output,
            analysis_file=self.analysis_output,
            fact_check_file=self.fact_check_output,
            title_hook_file=self.title_hook_output,
            script_file=self.script_output,
            topic_title=metadata["topic_title"],
            source_url=metadata["source_url"],
            category=metadata["category"],
        )

        validate_content_package(package_dir)

        self.content_package_output = package_dir

        return package_dir

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

            self.analysis_output = (
                research_analyzer_adapter
                .analyze_from_research(
                    self.research_output,
                    self.article_output,
                )
            )

            if self.analysis_output is None:
                raise RuntimeError(
                    "Analysis failed to produce an output."
                )

            return self.analysis_output

        def run_fact_check():
            if self.research_output is None:
                raise RuntimeError(
                    "Research output is unavailable for Fact Checker."
                )

            self.fact_check_output = (
                fact_checker_adapter
                .run_fact_check(self.research_output)
            )

            if self.fact_check_output is None:
                raise RuntimeError(
                    "Fact Checker failed to produce an output."
                )

            return self.fact_check_output

        def run_title_hook():
            if self.research_output is None:
                raise RuntimeError(
                    "Research output is unavailable for Title + Hook."
                )

            if self.fact_check_output is None:
                raise RuntimeError(
                    "Fact-check output is unavailable for Title + Hook."
                )

            self.title_hook_output = (
                title_hook_adapter
                .generate_title_hook(
                    self.research_output,
                    self.fact_check_output,
                )
            )

            if self.title_hook_output is None:
                raise RuntimeError(
                    "Title + Hook failed to produce an output."
                )

            return self.title_hook_output

        def run_script():
            if self.fact_check_output is None:
                raise RuntimeError(
                    "Fact-check output is unavailable for Script Writer."
                )

            if self.title_hook_output is None:
                raise RuntimeError(
                    "Title + Hook output is unavailable for Script Writer."
                )

            self.script_output = (
                script_writer_adapter
                .generate_script(
                    self.fact_check_output,
                    self.title_hook_output,
                )
            )

            if self.script_output is None:
                raise RuntimeError(
                    "Script Writer failed to produce an output."
                )

            return self.script_output

        return {
            "research": run_research,
            "article_extraction": run_article_extraction,
            "analysis": run_analysis,
            "fact_check": run_fact_check,
            "title_hook": run_title_hook,
            "script": run_script,
            "content_package": self.run_content_package,
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
            print(f"[{number}/{len(self.stages)}] {stage}")

        print("=" * 60)


def main():
    orchestrator = AIKhojOrchestrator()
    orchestrator.show_pipeline()
    stage_functions = orchestrator.build_stage_functions()

    if "--dry-run" in sys.argv:
        orchestrator.dry_run_pipeline(stage_functions)
        return

    orchestrator.run_pipeline(stage_functions)




if __name__ == "__main__":
    main()
