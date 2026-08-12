"""Fail-closed credential scanning for controlled benchmark artifacts."""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyarrow.parquet as parquet
from inspect_ai.log import read_eval_log

_CREDENTIAL_PATTERNS = (
    re.compile(rb"sk-or-v1-", re.IGNORECASE),
    re.compile(rb"\bauthorization\b(?:\\?[\"'])?\s*[:=]", re.IGNORECASE),
    re.compile(rb"\bOPENROUTER_API_KEY\b", re.IGNORECASE),
)


@dataclass(frozen=True, slots=True)
class Finding:
    """A safe-to-print artifact scanner finding."""

    relative_path: str
    reason: str


def _contains_credential_marker(content: bytes) -> bool:
    return any(pattern.search(content) is not None for pattern in _CREDENTIAL_PATTERNS)


def _json_default(value: object) -> object:
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).decode("latin-1")
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return isoformat()
    raise TypeError


def _eval_content(log: object) -> bytes:
    model_dump = getattr(log, "model_dump", None)
    payload = model_dump(mode="json") if callable(model_dump) else log
    return json.dumps(
        payload,
        default=_json_default,
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")


def _value_contains_credential_marker(value: Any) -> bool:
    if isinstance(value, str):
        return _contains_credential_marker(value.encode("utf-8"))
    if isinstance(value, (bytes, bytearray, memoryview)):
        return _contains_credential_marker(bytes(value))
    if isinstance(value, Mapping):
        return any(
            _value_contains_credential_marker(key) or _value_contains_credential_marker(item)
            for key, item in value.items()
        )
    if isinstance(value, Sequence):
        return any(_value_contains_credential_marker(item) for item in value)
    return False


def _parquet_contains_credential_marker(path: Path) -> bool:
    parquet_file = parquet.ParquetFile(path)
    for batch in parquet_file.iter_batches(batch_size=1_024):
        for column in batch.columns:
            for scalar in column:
                if _value_contains_credential_marker(scalar.as_py()):
                    return True
    return False


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix() or "."
    except ValueError:
        return "."


def _scan_file(path: Path, root: Path) -> list[Finding]:
    relative_path = _relative_path(path, root)
    if path.is_symlink():
        return [Finding(relative_path, "symbolic link is not allowed")]

    findings: list[Finding] = []
    try:
        raw_content = path.read_bytes()
    except OSError:
        return [Finding(relative_path, "unreadable file")]
    if _contains_credential_marker(raw_content):
        findings.append(Finding(relative_path, "credential marker in raw bytes"))

    if path.suffix.lower() == ".eval":
        try:
            parsed_content = _eval_content(read_eval_log(str(path)))
        except Exception:  # Structured evidence is untrusted and must fail closed.
            findings.append(Finding(relative_path, "unreadable eval"))
        else:
            if _contains_credential_marker(parsed_content):
                findings.append(Finding(relative_path, "credential marker in parsed eval content"))
    elif path.suffix.lower() == ".parquet":
        try:
            contains_marker = _parquet_contains_credential_marker(path)
        except Exception:  # Structured evidence is untrusted and must fail closed.
            findings.append(Finding(relative_path, "unreadable parquet"))
        else:
            if contains_marker:
                findings.append(
                    Finding(relative_path, "credential marker in parsed parquet content")
                )
    return findings


def scan_artifacts(root: str | Path) -> list[Finding]:
    """Scan every regular file below ``root`` and return safe findings."""

    root_path = Path(root)
    if not root_path.is_dir():
        return [Finding(".", "artifact root is not a directory")]

    findings: list[Finding] = []

    def record_walk_error(error: OSError) -> None:
        error_path = Path(error.filename) if error.filename else root_path
        findings.append(Finding(_relative_path(error_path, root_path), "unreadable directory"))

    for directory, directory_names, file_names in os.walk(
        root_path,
        topdown=True,
        onerror=record_walk_error,
        followlinks=False,
    ):
        directory_path = Path(directory)
        retained_directories: list[str] = []
        for name in sorted(directory_names):
            candidate = directory_path / name
            if candidate.is_symlink():
                findings.append(
                    Finding(_relative_path(candidate, root_path), "symbolic link is not allowed")
                )
            else:
                retained_directories.append(name)
        directory_names[:] = retained_directories
        for name in sorted(file_names):
            findings.extend(_scan_file(directory_path / name, root_path))
    return sorted(findings, key=lambda finding: (finding.relative_path, finding.reason))


def main(argv: Sequence[str] | None = None) -> int:
    """Run the scanner without ever rendering artifact or exception content."""

    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1:
        print(".: expected exactly one artifact root", file=sys.stderr)
        return 2
    try:
        findings = scan_artifacts(arguments[0])
    except Exception:  # The command itself is also fail closed.
        print(".: scanner failure", file=sys.stderr)
        return 2
    for finding in findings:
        print(f"{finding.relative_path}: {finding.reason}", file=sys.stderr)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
