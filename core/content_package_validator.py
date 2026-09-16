"""AI Khoj Content Package v1 validator.

Validates a completed Content Package without modifying it.

No Gemini/API calls belong here.
"""

import json
from pathlib import Path

from core.contracts.content_package import (
    REQUIRED_ARTIFACTS,
    SCHEMA_VERSION,
)


def _load_package_json(package_dir: Path) -> dict:
    package_file = package_dir / "package.json"

    if not package_file.is_file():
        raise FileNotFoundError(
            f"package.json not found: {package_file}"
        )

    try:
        return json.loads(
            package_file.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid package.json: {package_file}"
        ) from exc


def _validate_basic_metadata(data: dict) -> None:
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported schema version: "
            f"{data.get('schema_version')}"
        )

    if not isinstance(data.get("package_id"), str):
        raise ValueError("package_id must be a string.")

    if not data["package_id"].strip():
        raise ValueError("package_id cannot be empty.")

    if not isinstance(data.get("created_at"), str):
        raise ValueError("created_at must be a string.")

    topic = data.get("topic")

    if not isinstance(topic, dict):
        raise ValueError("topic must be an object.")

    for field in ("title", "source_url", "category"):
        value = topic.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"topic.{field} must be a non-empty string."
            )


def _validate_artifacts(
    package_dir: Path,
    artifacts: dict,
) -> None:
    if not isinstance(artifacts, dict):
        raise ValueError("artifacts must be an object.")

    missing = [
        name
        for name in REQUIRED_ARTIFACTS
        if name not in artifacts
    ]

    if missing:
        raise ValueError(
            "Missing required artifacts: "
            + ", ".join(missing)
        )

    package_root = package_dir.resolve()

    for name in REQUIRED_ARTIFACTS:
        artifact = artifacts[name]

        if not isinstance(artifact, dict):
            raise ValueError(
                f"Artifact '{name}' must be an object."
            )

        path_value = artifact.get("path")
        status = artifact.get("status")

        if not isinstance(path_value, str) or not path_value.strip():
            raise ValueError(
                f"Artifact '{name}' has invalid path."
            )

        if status != "success":
            raise ValueError(
                f"Artifact '{name}' status must be 'success'."
            )

        artifact_path = Path(path_value).resolve()

        try:
            artifact_path.relative_to(package_root)
        except ValueError as exc:
            raise ValueError(
                f"Artifact '{name}' points outside the package: "
                f"{path_value}"
            ) from exc

        if not artifact_path.is_file():
            raise FileNotFoundError(
                f"Artifact '{name}' file not found: "
                f"{artifact_path}"
            )

        if artifact_path.stat().st_size == 0:
            raise ValueError(
                f"Artifact '{name}' is empty: {artifact_path}"
            )


def _validate_quality(data: dict) -> None:
    quality = data.get("quality")

    if not isinstance(quality, dict):
        raise ValueError("quality must be an object.")

    for field in (
        "fact_check_ready",
        "script_ready",
        "package_ready",
    ):
        if not isinstance(quality.get(field), bool):
            raise ValueError(
                f"quality.{field} must be boolean."
            )

    if quality["package_ready"]:
        if not quality["fact_check_ready"]:
            raise ValueError(
                "package_ready cannot be true when "
                "fact_check_ready is false."
            )

        if not quality["script_ready"]:
            raise ValueError(
                "package_ready cannot be true when "
                "script_ready is false."
            )


def validate_content_package(package_dir) -> bool:
    """Validate a Content Package v1 directory.

    Returns True when the complete package satisfies the contract.
    Raises a descriptive exception otherwise.
    """

    package_dir = Path(package_dir)

    if not package_dir.is_dir():
        raise FileNotFoundError(
            f"Content package directory not found: {package_dir}"
        )

    data = _load_package_json(package_dir)

    _validate_basic_metadata(data)
    _validate_artifacts(
        package_dir,
        data.get("artifacts"),
    )
    _validate_quality(data)

    return True
