"""Fail closed when a GitHub Actions workflow is not valid YAML."""

from __future__ import annotations

from pathlib import Path
import sys

import yaml

REQUIRED_TOP_LEVEL_KEYS = frozenset({"name", "on", "jobs"})


def validate_workflow(path: Path) -> list[str]:
    """Return structural YAML errors for one workflow file."""

    try:
        with path.open(encoding="utf-8") as handle:
            document = yaml.load(handle, Loader=yaml.BaseLoader)
    except (OSError, yaml.YAMLError) as exc:
        return [f"{path}: {exc}"]

    if not isinstance(document, dict):
        return [f"{path}: expected a top-level mapping"]

    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL_KEYS.difference(document))
    if missing:
        errors.append(f"{path}: missing top-level keys: {', '.join(missing)}")

    jobs = document.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        errors.append(f"{path}: jobs must be a non-empty mapping")

    return errors


def main() -> int:
    workflow_dir = Path(".github/workflows")
    workflow_paths = sorted(
        [*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")]
    )
    if not workflow_paths:
        print("No GitHub workflow files found.", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in workflow_paths:
        errors.extend(validate_workflow(path))

    if errors:
        print("Invalid GitHub workflow configuration:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(workflow_paths)} GitHub workflow files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
