"""AI Khoj Content Package v1 builder.

Builds a self-contained package from validated pipeline artifacts.

This module performs deterministic file operations only.
No Gemini/API calls belong here.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

from core.contracts.content_package import (
    ArtifactRef,
    ContentPackage,
    PackageMetadata,
    QualityStatus,
    TopicMetadata,
    SCHEMA_VERSION,
)


OUTPUT_ROOT = Path("outputs/content_packages")


def _validate_source(path: Path, name: str) -> None:
    """Validate that a source artifact exists and is non-empty."""

    if not path.is_file():
        raise FileNotFoundError(
            f"Required artifact not found for '{name}': {path}"
        )

    if path.stat().st_size == 0:
        raise ValueError(
            f"Required artifact is empty for '{name}': {path}"
        )


def _build_package_id(timestamp: datetime) -> str:
    return f"content_{timestamp.strftime('%Y%m%d_%H%M%S')}"


def build_content_package(
    research_file,
    article_file,
    analysis_file,
    fact_check_file,
    title_hook_file,
    script_file,
    topic_title,
    source_url,
    category="ai",
    output_root=OUTPUT_ROOT,
):
    """Build and return a Content Package v1 directory."""

    sources = {
        "research": Path(research_file),
        "article": Path(article_file),
        "analysis": Path(analysis_file),
        "fact_check": Path(fact_check_file),
        "title_hook": Path(title_hook_file),
        "script": Path(script_file),
    }

    for name, path in sources.items():
        _validate_source(path, name)

    timestamp = datetime.now()
    package_id = _build_package_id(timestamp)
    package_dir = Path(output_root) / package_id

    if package_dir.exists():
        raise FileExistsError(
            f"Package directory already exists: {package_dir}"
        )

    package_dir.mkdir(parents=True)

    artifact_paths = {}

    try:
        for name, source_path in sources.items():
            destination = package_dir / source_path.name
            shutil.copy2(source_path, destination)
            artifact_paths[name] = ArtifactRef(
                path=str(destination),
                status="success",
            )

        package = ContentPackage(
            package_id=package_id,
            created_at=timestamp.isoformat(),
            topic=TopicMetadata(
                title=topic_title,
                source_url=source_url,
                category=category,
            ),
            artifacts=artifact_paths,
            quality=QualityStatus(
                fact_check_ready=True,
                script_ready=True,
                package_ready=True,
            ),
            metadata=PackageMetadata(),
            schema_version=SCHEMA_VERSION,
        )

        package.validate_structure()

        package_json = {
            "schema_version": package.schema_version,
            "package_id": package.package_id,
            "created_at": package.created_at,
            "topic": {
                "title": package.topic.title,
                "source_url": package.topic.source_url,
                "category": package.topic.category,
            },
            "artifacts": {
                name: {
                    "path": artifact.path,
                    "status": artifact.status,
                }
                for name, artifact in package.artifacts.items()
            },
            "quality": {
                "fact_check_ready": package.quality.fact_check_ready,
                "script_ready": package.quality.script_ready,
                "package_ready": package.quality.package_ready,
            },
            "metadata": {
                "language": package.metadata.language,
                "content_type": package.metadata.content_type,
                "pipeline_version": package.metadata.pipeline_version,
            },
        }

        package_file = package_dir / "package.json"
        package_file.write_text(
            json.dumps(package_json, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return package_dir

    except Exception:
        shutil.rmtree(package_dir, ignore_errors=True)
        raise
