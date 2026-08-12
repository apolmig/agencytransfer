from __future__ import annotations

import json
import stat
import zipfile
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import atb_eval.offline_revalidation as offline
import pytest

MANIFEST_HASH = "a" * 64
EXECUTION_COMMIT = "b" * 40
VALIDATION_COMMIT = "c" * 40
EXECUTION_LOCK = "d" * 64
VALIDATION_LOCK = "e" * 64
ARTIFACT_HASH = "f" * 64
EXECUTION_ID = "1" * 32
ARTIFACT_METADATA = {
    "sha256": ARTIFACT_HASH,
    "size_bytes": 100,
    "member_count": 3,
    "uncompressed_bytes": 200,
    "inventory_sha256": "8" * 64,
    "checksums_verified": True,
}


def _historical_receipt() -> dict[str, object]:
    return {
        "schema_version": "atb-controlled-canary-receipt-v0.1",
        "protocol_id": "atb-test-v0.1",
        "manifest_sha256": MANIFEST_HASH,
        "public_commit": EXECUTION_COMMIT,
        "source_commit": "9" * 40,
        "workflow_actor": "tester",
        "workflow_run_id": "31622800735",
        "paid_step_outcome": "failure",
        "planned_run_cost_envelope_usd": 0.04,
        "provider_key_lifetime_cap_usd": 30.0,
        "recorded_at": "2026-08-12T17:29:27Z",
    }


def _write_archive(
    path: Path,
    files: dict[str, bytes],
    *,
    checksummed_files: dict[str, bytes] | None = None,
) -> str:
    covered = files if checksummed_files is None else checksummed_files
    checksum_lines = "".join(
        f"{sha256(content).hexdigest()}  ./{name}\n" for name, content in sorted(covered.items())
    ).encode()
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("checksums.sha256", checksum_lines)
        for name, content in files.items():
            archive.writestr(name, content)
    return sha256(path.read_bytes()).hexdigest()


def _condition() -> SimpleNamespace:
    return SimpleNamespace(
        condition_id="acme-provider-fp8",
        model="openrouter/acme/model",
    )


def _manifest() -> SimpleNamespace:
    return SimpleNamespace(
        protocol_id="atb-test-v0.1",
        models=[_condition()],
        model_roles={},
        dataset=SimpleNamespace(source_revision="9" * 40),
        run=SimpleNamespace(
            planned_run_cost_envelope_usd=0.04,
            provider_key_limit_usd=30.0,
        ),
    )


def _metadata(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "atb_protocol_id": "atb-test-v0.1",
        "atb_manifest_sha256": MANIFEST_HASH,
        "atb_code_commit": EXECUTION_COMMIT,
        "atb_code_dirty": False,
        "atb_environment_lock_sha256": EXECUTION_LOCK,
        "atb_execution_id": EXECUTION_ID,
        "atb_openrouter_route_receipt_sha256": "2" * 64,
    }
    values.update(overrides)
    return values


def _log(metadata: dict[str, object] | None = None) -> SimpleNamespace:
    return SimpleNamespace(eval=SimpleNamespace(metadata=metadata or _metadata()))


def test_execution_context_requires_consistent_clean_persisted_provenance() -> None:
    context = offline.execution_context_from_logs(
        [_log(), _log()], _manifest(), MANIFEST_HASH, EXECUTION_COMMIT
    )
    assert context == {
        "code_commit": EXECUTION_COMMIT,
        "code_dirty": False,
        "environment_lock_sha256": EXECUTION_LOCK,
        "execution_id": EXECUTION_ID,
        "openrouter_route_receipt_sha256": "2" * 64,
    }

    with pytest.raises(ValueError, match="inconsistent"):
        offline.execution_context_from_logs(
            [_log(), _log(_metadata(atb_execution_id="3" * 32))],
            _manifest(),
            MANIFEST_HASH,
            EXECUTION_COMMIT,
        )
    with pytest.raises(ValueError, match="clean original execution"):
        offline.execution_context_from_logs(
            [_log(_metadata(atb_code_dirty=True))],
            _manifest(),
            MANIFEST_HASH,
            EXECUTION_COMMIT,
        )


def test_receipt_records_original_failure_and_separate_corrected_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    eval_path = tmp_path / "evidence.eval"
    eval_path.write_bytes(b"content-addressed eval bytes")
    capture_dir = tmp_path / "openrouter-route-capture"
    capture_dir.mkdir()
    (capture_dir / "receipt.json").write_text("{}\n", encoding="utf-8")
    logs = [_log()]
    monkeypatch.setattr(
        offline, "load_manifest_with_hash", lambda unused: (_manifest(), MANIFEST_HASH)
    )
    monkeypatch.setattr(offline, "_load_evidence_logs", lambda unused: ([eval_path], logs))
    route_calls: list[tuple[object, ...]] = []

    def verify_route(*args: object, **kwargs: object) -> dict[str, object]:
        route_calls.append((*args, kwargs))
        return {"receipt_sha256": "2" * 64, "artifact_count": 2}

    monkeypatch.setattr(
        offline,
        "verify_persisted_openrouter_route_capture",
        verify_route,
    )
    monkeypatch.setattr(
        offline,
        "controlled_usage_summary",
        lambda unused: {
            "schema_version": "atb-controlled-usage-summary-v0.1",
            "eval_log_count": 1,
            "inspect_tokens": 10,
            "inspect_estimated_cost_usd": 0.001,
            "openrouter_billed_cost_usd": 0.001,
            "conditions": [],
        },
    )
    validator_calls: list[tuple[object, ...]] = []

    def accept(*args: object, **kwargs: object) -> bool:
        validator_calls.append((*args, kwargs))
        return True

    monkeypatch.setattr(offline.runner, "validate_persisted_execution", accept, raising=False)
    monkeypatch.setattr(
        offline, "_historical_receipt", lambda *args, **kwargs: _historical_receipt()
    )
    monkeypatch.setattr(offline.artifact_scan, "scan_artifacts", lambda unused: [])
    receipt = offline.build_revalidation_receipt(
        manifest_path=tmp_path / "manifest.json",
        artifact_root=tmp_path,
        log_root=tmp_path,
        execution_commit=EXECUTION_COMMIT,
        validation_commit=VALIDATION_COMMIT,
        validation_environment_lock_sha256=VALIDATION_LOCK,
        artifact_sha256=ARTIFACT_HASH,
        artifact_archive_metadata=ARTIFACT_METADATA,
        workflow_run_id="31622800735",
    )
    assert receipt["original_paid_step_outcome"] == "failure"
    assert receipt["corrected_postflight_acceptance"] is True
    assert receipt["controlled_evidence_accepted"] is True
    assert receipt["evidence_scope"] == "transport_canary_only"
    assert receipt["scientific_claim_eligible"] is False
    assert receipt["execution"]["code_commit"] == EXECUTION_COMMIT
    assert receipt["validation"]["code_commit"] == VALIDATION_COMMIT
    assert receipt["artifact"]["sha256"] == ARTIFACT_HASH
    assert receipt["artifact"]["checksums_verified"] is True
    assert receipt["artifact"]["sha256_source"] == "locally_verified_archive"
    assert receipt["artifact"]["scanner_status"] == "passed"
    assert receipt["artifact"]["scanner_status_source"] == "local_revalidation"
    assert receipt["source"] == "local_revalidation"
    assert (
        receipt["execution"]["eval_logs"][0]["sha256"] == sha256(eval_path.read_bytes()).hexdigest()
    )
    assert len(validator_calls) == 1
    validator_kwargs = validator_calls[0][-1]
    assert validator_kwargs == {
        "execution_id": EXECUTION_ID,
        "route_receipt_sha256": "2" * 64,
    }
    assert len(route_calls) == 1
    assert route_calls[0][1] == capture_dir
    assert route_calls[0][-1] == {
        "manifest_sha256": MANIFEST_HASH,
        "expected_receipt_sha256": "2" * 64,
    }
    rendered = json.dumps(receipt)
    assert "prompt" not in rendered
    assert "response body" not in rendered


def test_content_addressed_writer_emits_full_file_hash_sidecar(tmp_path: Path) -> None:
    output = tmp_path / "receipt.json"
    digest = offline.write_content_addressed_receipt(output, {"accepted": True})
    assert digest == sha256(output.read_bytes()).hexdigest()
    assert (tmp_path / "receipt.json.sha256").read_text(encoding="utf-8") == (
        f"{digest}  receipt.json\n"
    )
    with pytest.raises(ValueError, match="written safely"):
        offline.write_content_addressed_receipt(output, {"accepted": True})


def test_cli_failure_never_renders_exception_or_writes_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "receipt.json"
    args = SimpleNamespace(
        manifest=tmp_path / "manifest.json",
        artifact_archive=tmp_path / "artifact.zip",
        log_root="logs",
        execution_commit=EXECUTION_COMMIT,
        validation_commit=VALIDATION_COMMIT,
        artifact_sha256=ARTIFACT_HASH,
        workflow_run_id="31622800735",
        output=output,
    )
    monkeypatch.setattr(offline, "parse_args", lambda argv: args)
    monkeypatch.setattr(
        offline.runner,
        "repository_provenance",
        lambda unused: (_ for _ in ()).throw(ValueError("secret response body")),
    )
    assert offline.main([]) == 2
    captured = capsys.readouterr()
    assert captured.err == "offline postflight revalidation failed safely\n"
    assert "secret" not in captured.err
    assert not output.exists()


def test_cli_requires_archive_and_relative_log_root(tmp_path: Path) -> None:
    arguments = offline.parse_args(
        [
            "--manifest",
            str(tmp_path / "manifest.json"),
            "--artifact-archive",
            str(tmp_path / "artifact.zip"),
            "--log-root",
            "logs",
            "--execution-commit",
            EXECUTION_COMMIT,
            "--validation-commit",
            VALIDATION_COMMIT,
            "--artifact-sha256",
            ARTIFACT_HASH,
            "--workflow-run-id",
            "31622800735",
            "--output",
            str(tmp_path / "receipt.json"),
        ]
    )
    assert arguments.artifact_archive == tmp_path / "artifact.zip"
    assert arguments.log_root == "logs"
    assert not hasattr(arguments, "artifact_scanner_status")
    assert not hasattr(arguments, "original_paid_step_outcome")


def test_archive_sha256_must_be_locally_verified(tmp_path: Path) -> None:
    archive = tmp_path / "artifact.zip"
    actual = _write_archive(archive, {"receipt.json": b"{}"})
    assert actual != ARTIFACT_HASH
    with pytest.raises(ValueError, match="does not match"):
        offline._extract_verified_archive(archive, ARTIFACT_HASH, tmp_path / "out")


def test_archive_rejects_zip_slip(tmp_path: Path) -> None:
    archive = tmp_path / "artifact.zip"
    digest = _write_archive(archive, {"../escape": b"no"})
    with pytest.raises(ValueError, match="unsafe member path"):
        offline._extract_verified_archive(archive, digest, tmp_path / "out")
    assert not (tmp_path / "escape").exists()


def test_archive_rejects_symlink_member(tmp_path: Path) -> None:
    archive = tmp_path / "artifact.zip"
    with zipfile.ZipFile(archive, "w") as output:
        link = zipfile.ZipInfo("link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        output.writestr(link, "target")
    digest = sha256(archive.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="non-regular"):
        offline._extract_verified_archive(archive, digest, tmp_path / "out")


def test_archive_rejects_duplicate_casefolded_member(tmp_path: Path) -> None:
    archive = tmp_path / "artifact.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("A.txt", "first")
        output.writestr("a.TXT", "second")
    digest = sha256(archive.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="duplicate"):
        offline._extract_verified_archive(archive, digest, tmp_path / "out")


def test_archive_rejects_altered_checked_log(tmp_path: Path) -> None:
    archive = tmp_path / "artifact.zip"
    digest = _write_archive(
        archive,
        {"logs/evidence.eval": b"altered"},
        checksummed_files={"logs/evidence.eval": b"original"},
    )
    with pytest.raises(ValueError, match="checksum verification failed"):
        offline._extract_verified_archive(archive, digest, tmp_path / "out")


def test_archive_extracts_exact_checksum_inventory(tmp_path: Path) -> None:
    archive = tmp_path / "artifact.zip"
    receipt = json.dumps(_historical_receipt()).encode()
    files = {"receipt.json": receipt, "logs/evidence.eval": b"opaque-eval"}
    digest = _write_archive(archive, files)
    root = tmp_path / "out"
    verification = offline._extract_verified_archive(archive, digest, root)
    assert verification["sha256"] == digest
    assert verification["checksums_verified"] is True
    assert verification["member_count"] == 3
    assert (root / "receipt.json").read_bytes() == receipt
    assert (root / "logs/evidence.eval").read_bytes() == b"opaque-eval"


def test_local_scanner_rejects_secret_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "receipt.json").write_text(json.dumps(_historical_receipt()), encoding="utf-8")
    (tmp_path / "secret.txt").write_text("OPENROUTER_API_KEY=redacted", encoding="utf-8")
    monkeypatch.setattr(
        offline, "load_manifest_with_hash", lambda unused: (_manifest(), MANIFEST_HASH)
    )
    with pytest.raises(ValueError, match="local artifact scan"):
        offline.build_revalidation_receipt(
            manifest_path=tmp_path / "manifest.json",
            artifact_root=tmp_path,
            log_root=tmp_path,
            execution_commit=EXECUTION_COMMIT,
            validation_commit=VALIDATION_COMMIT,
            validation_environment_lock_sha256=VALIDATION_LOCK,
            artifact_sha256=ARTIFACT_HASH,
            artifact_archive_metadata=ARTIFACT_METADATA,
            workflow_run_id="31622800735",
        )


def test_eval_input_hardlink_is_rejected(tmp_path: Path) -> None:
    first = tmp_path / "first.eval"
    first.write_bytes(b"opaque")
    second = tmp_path / "second.eval"
    second.hardlink_to(first)
    with pytest.raises(ValueError, match="single-link"):
        offline._load_evidence_logs(tmp_path)


def test_archive_rejects_unsupported_compression(tmp_path: Path) -> None:
    archive = tmp_path / "artifact.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_BZIP2) as output:
        output.writestr("checksums.sha256", b"")
    digest = sha256(archive.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="unsupported ZIP features"):
        offline._extract_verified_archive(archive, digest, tmp_path / "out")


def test_relative_log_root_rejects_eval_outside_selection(tmp_path: Path) -> None:
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "inside.eval").write_bytes(b"inside")
    (tmp_path / "outside.eval").write_bytes(b"outside")
    with pytest.raises(ValueError, match="outside"):
        offline._relative_log_root(tmp_path, "logs")


def test_historical_receipt_rejects_non_finite_number(tmp_path: Path) -> None:
    payload = json.dumps(_historical_receipt()).replace("0.04", "NaN")
    (tmp_path / "receipt.json").write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError, match="non-finite"):
        offline._historical_receipt(
            tmp_path,
            expected_workflow_run_id="31622800735",
            expected_execution_commit=EXECUTION_COMMIT,
        )
