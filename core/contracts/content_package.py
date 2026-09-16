"""AI Khoj Content Package v1 contract.

This module defines the stable handoff contract between the
Knowledge -> Script pipeline and future production agents.

No AI/API calls belong in this module.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


SCHEMA_VERSION = "1.0"


REQUIRED_ARTIFACTS = (
    "research",
    "article",
    "analysis",
    "fact_check",
    "title_hook",
    "script",
)


@dataclass(frozen=True)
class ArtifactRef:
    """Reference to one validated content artifact."""

    path: str
    status: str = "success"

    def validate(self) -> None:
        if not self.path.strip():
            raise ValueError("Artifact path cannot be empty.")

        if self.status != "success":
            raise ValueError(
                f"Artifact status must be 'success', got: {self.status}"
            )

        if not Path(self.path).is_file():
            raise FileNotFoundError(
                f"Artifact file does not exist: {self.path}"
            )


@dataclass(frozen=True)
class TopicMetadata:
    """Topic-level metadata shared by the content package."""

    title: str
    source_url: str
    category: str


@dataclass(frozen=True)
class QualityStatus:
    """Deterministic readiness state of the package."""

    fact_check_ready: bool
    script_ready: bool
    package_ready: bool


@dataclass(frozen=True)
class PackageMetadata:
    """General metadata describing the package."""

    language: str = "hinglish"
    content_type: str = "youtube_documentary"
    pipeline_version: str = "1.0"


@dataclass(frozen=True)
class ContentPackage:
    """Stable Content Package v1 contract.

    The package contains references to validated artifacts rather than
    duplicating their actual content.
    """

    package_id: str
    created_at: str
    topic: TopicMetadata
    artifacts: dict[str, ArtifactRef]
    quality: QualityStatus
    metadata: PackageMetadata
    schema_version: str = SCHEMA_VERSION

    def validate_structure(self) -> None:
        """Validate the structural contract without changing any files."""

        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported schema version: {self.schema_version}"
            )

        if not self.package_id.strip():
            raise ValueError("package_id cannot be empty.")

        if not self.created_at.strip():
            raise ValueError("created_at cannot be empty.")

        try:
            datetime.fromisoformat(self.created_at)
        except ValueError as exc:
            raise ValueError(
                f"created_at must be valid ISO-8601: {self.created_at}"
            ) from exc

        if not self.topic.title.strip():
            raise ValueError("Topic title cannot be empty.")

        if not self.topic.source_url.strip():
            raise ValueError("Topic source_url cannot be empty.")

        missing = [
            name
            for name in REQUIRED_ARTIFACTS
            if name not in self.artifacts
        ]

        if missing:
            raise ValueError(
                f"Missing required artifacts: {', '.join(missing)}"
            )

        for name in REQUIRED_ARTIFACTS:
            self.artifacts[name].validate()

    def is_ready(self) -> bool:
        """Return whether the package is production-ready."""

        return (
            self.quality.fact_check_ready
            and self.quality.script_ready
            and self.quality.package_ready
        )
