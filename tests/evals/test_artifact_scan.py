from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as parquet
from atb_eval import artifact_scan


def test_parsed_eval_marker_is_detected_when_absent_from_raw_bytes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    eval_path = tmp_path / "nested" / "sample.eval"
    eval_path.parent.mkdir()
    eval_path.write_bytes(b"compressed evidence without a visible marker")
    monkeypatch.setattr(
        artifact_scan,
        "read_eval_log",
        lambda _path: {"message": "sk-or-v1-hidden-in-decoded-log"},
    )

    findings = artifact_scan.scan_artifacts(tmp_path)

    assert (
        artifact_scan.Finding(
            "nested/sample.eval",
            "credential marker in parsed eval content",
        )
        in findings
    )


def test_clean_structured_files_pass(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "clean.eval").write_bytes(b"opaque clean eval")
    monkeypatch.setattr(
        artifact_scan,
        "read_eval_log",
        lambda _path: {"messages": [{"content": "ordinary benchmark response"}]},
    )
    parquet.write_table(
        pa.table({"content": ["ordinary scanner result"]}),
        tmp_path / "clean.parquet",
        compression="gzip",
        write_statistics=False,
    )

    assert artifact_scan.scan_artifacts(tmp_path) == []


def test_unreadable_eval_fails_closed_without_printing_exception_detail(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    (tmp_path / "broken.eval").write_bytes(b"opaque eval")

    def unreadable(_path: str) -> object:
        raise ValueError("sk-or-v1-secret-from-exception")

    monkeypatch.setattr(artifact_scan, "read_eval_log", unreadable)

    exit_code = artifact_scan.main([str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "broken.eval: unreadable eval\n"
    assert "secret-from-exception" not in captured.err


def test_unreadable_parquet_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "broken.parquet").write_bytes(b"not a parquet file")

    assert artifact_scan.Finding("broken.parquet", "unreadable parquet") in (
        artifact_scan.scan_artifacts(tmp_path)
    )


def test_marker_in_compressed_parquet_cell_is_detected(tmp_path: Path) -> None:
    parquet_path = tmp_path / "scout.parquet"
    marker = "sk-or-v1-hidden-in-compressed-cell"
    parquet.write_table(
        pa.table({"result": [marker]}),
        parquet_path,
        compression="gzip",
        write_statistics=False,
    )
    assert b"sk-or-v1-" not in parquet_path.read_bytes()

    findings = artifact_scan.scan_artifacts(tmp_path)

    assert (
        artifact_scan.Finding(
            "scout.parquet",
            "credential marker in parsed parquet content",
        )
        in findings
    )


def test_raw_authorization_header_and_environment_variable_are_detected(tmp_path: Path) -> None:
    (tmp_path / "headers.txt").write_text(
        '"Authorization": "Bearer redacted"\nOPENROUTER_API_KEY=redacted\n',
        encoding="utf-8",
    )

    assert artifact_scan.Finding("headers.txt", "credential marker in raw bytes") in (
        artifact_scan.scan_artifacts(tmp_path)
    )
