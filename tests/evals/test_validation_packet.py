from __future__ import annotations

import json
import stat
from pathlib import Path

import atb_eval.validation_packet as packet
import pytest
from atb_eval.manifest import load_manifest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _key(path: Path, *, mode: int = 0o600) -> Path:
    path.write_bytes(bytes(range(32)))
    path.chmod(mode)
    return path


def _frame() -> packet.ExecutionFrame:
    manifest = load_manifest(REPO_ROOT / "evals/manifests/diselect-wave1a-v0.3.json")
    items: list[packet.FrameItem] = []
    index = 0
    for condition in manifest.models:
        for use_case in ("voting", "mps", "baseline"):
            for offset in range(10):
                index += 1
                items.append(
                    packet.FrameItem(
                        condition_id=condition.condition_id,
                        sample_id=f"sample-{index:03d}",
                        epoch=1,
                        stratum=(condition.condition_id, use_case),
                        request=f"Synthetic review request {index}",
                        response=f"Synthetic review response {index} / {offset}",
                    )
                )
    return packet.ExecutionFrame(
        manifest=manifest,
        manifest_sha256="a" * 64,
        execution_id="1" * 32,
        code_commit="b" * 40,
        evidence_inventory_sha256="c" * 64,
        items=tuple(items),
    )


def test_packet_generation_is_blind_private_and_differently_ordered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(packet, "_validated_frame", lambda *unused: _frame())
    output = tmp_path / "packets"
    result = packet.create_validation_packets(
        manifest_path=REPO_ROOT / "evals/manifests/diselect-wave1a-v0.3.json",
        log_dir=tmp_path / "logs",
        key_file=_key(tmp_path / "hmac.key"),
        output_dir=output,
        reviewer_pseudonyms=["reviewer-a", "reviewer-b"],
    )

    assert result.item_count == 30
    assert stat.S_IMODE(output.stat().st_mode) == 0o700
    assert {path.name for path in output.iterdir()} == {
        "reviewer-a.json",
        "reviewer-b.json",
        "private-map.json",
        "codebook.md",
    }
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in output.iterdir())

    first = json.loads((output / "reviewer-a.json").read_text(encoding="utf-8"))
    second = json.loads((output / "reviewer-b.json").read_text(encoding="utf-8"))
    assert first["independent_read_attested"] is False
    assert first["blinded_fields"] == list(packet.BLINDED_FIELDS)
    assert [item["review_item_id"] for item in first["items"]] != [
        item["review_item_id"] for item in second["items"]
    ]
    assert {item["review_item_id"] for item in first["items"]} == {
        item["review_item_id"] for item in second["items"]
    }
    rendered = json.dumps(first)
    assert "condition_id" not in rendered
    assert "automated_class" not in rendered
    assert "provider" not in {key for item in first["items"] for key in item}
    assert all(item["native_class"] is None for item in first["items"])

    private = packet.PrivateMap.model_validate_json(
        (output / "private-map.json").read_text(encoding="utf-8")
    )
    assert private.packet_set_id == result.packet_set_id
    assert private.item_count == 30
    assert {item.condition_id for item in private.items} == {
        condition.condition_id for condition in _frame().manifest.models
    }


def test_packet_generation_rejects_existing_output_and_weak_key_permissions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(packet, "_validated_frame", lambda *unused: _frame())
    existing = tmp_path / "existing"
    existing.mkdir(mode=0o700)
    with pytest.raises(ValueError, match="must not exist"):
        packet.create_validation_packets(
            manifest_path=REPO_ROOT / "evals/manifests/diselect-wave1a-v0.3.json",
            log_dir=tmp_path / "logs",
            key_file=_key(tmp_path / "key-a"),
            output_dir=existing,
            reviewer_pseudonyms=["reviewer-a", "reviewer-b"],
        )

    with pytest.raises(ValueError, match="owner-only"):
        packet.create_validation_packets(
            manifest_path=REPO_ROOT / "evals/manifests/diselect-wave1a-v0.3.json",
            log_dir=tmp_path / "logs",
            key_file=_key(tmp_path / "key-b", mode=0o644),
            output_dir=tmp_path / "new-output",
            reviewer_pseudonyms=["reviewer-a", "reviewer-b"],
        )


def test_packet_cli_failure_does_not_render_sensitive_exception(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail(**unused: object) -> packet.PrivateMap:
        raise ValueError("sensitive response text")

    monkeypatch.setattr(packet, "create_validation_packets", fail)
    status = packet.main(
        [
            "--manifest",
            str(tmp_path / "manifest.json"),
            "--log-dir",
            str(tmp_path / "logs"),
            "--key-file",
            str(tmp_path / "key"),
            "--output-dir",
            str(tmp_path / "output"),
            "--reviewer",
            "reviewer-a",
            "--reviewer",
            "reviewer-b",
        ]
    )
    captured = capsys.readouterr()
    assert status == 1
    assert captured.out == ""
    assert captured.err == "validation packet generation failed safely\n"
    assert "sensitive" not in captured.err


def test_persisted_route_capture_follows_the_eval_execution_directory(
    tmp_path: Path,
) -> None:
    log_root = tmp_path / "logs"
    execution_dir = log_root / "execution-123"
    eval_paths = [execution_dir / "first.eval", execution_dir / "second.eval"]

    assert packet._persisted_route_capture_dir(eval_paths) == (
        execution_dir / "openrouter-route-capture"
    )


def test_persisted_route_capture_rejects_mixed_execution_directories(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="share one execution directory"):
        packet._persisted_route_capture_dir(
            [
                tmp_path / "run-a" / "first.eval",
                tmp_path / "run-b" / "second.eval",
            ]
        )


def test_validated_frame_reads_route_capture_beside_nested_eval_logs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = _frame().manifest
    log_root = tmp_path / "logs"
    execution_dir = log_root / "execution-123"
    execution_dir.mkdir(parents=True)
    eval_paths = [execution_dir / "first.eval", execution_dir / "second.eval"]
    for path in eval_paths:
        path.write_bytes(b"persisted-eval")

    class FakeLog:
        def __init__(self, condition_id: str) -> None:
            self.condition_id = condition_id
            self.samples: list[object] = []

    condition_ids = [condition.condition_id for condition in manifest.models]
    fake_logs = {
        eval_paths[0]: FakeLog(condition_ids[0]),
        eval_paths[1]: FakeLog(condition_ids[1]),
    }
    captured_route_dirs: list[Path] = []

    monkeypatch.setattr(packet, "verify_committed_file", lambda *unused: None)
    monkeypatch.setattr(
        packet, "load_manifest_with_hash", lambda unused: (manifest, "a" * 64)
    )
    monkeypatch.setattr(
        packet, "_evidence_inventory", lambda unused: ((), "c" * 64)
    )
    monkeypatch.setattr(
        packet.runner, "read_postflight_log", lambda path: fake_logs[path]
    )
    monkeypatch.setattr(
        packet, "_consistent_log_metadata", lambda *unused: "b" * 40
    )
    monkeypatch.setattr(
        packet,
        "execution_context_from_logs",
        lambda *unused: {
            "openrouter_route_receipt_sha256": "d" * 64,
            "code_commit": "b" * 40,
            "code_dirty": False,
            "environment_lock_sha256": "e" * 64,
            "execution_id": "1" * 32,
        },
    )
    monkeypatch.setattr(
        packet,
        "verify_persisted_openrouter_route_capture",
        lambda unused_manifest, route_dir, **unused: captured_route_dirs.append(
            route_dir
        ),
    )
    monkeypatch.setattr(
        packet.runner, "validate_persisted_execution", lambda *unused, **kwargs: True
    )
    monkeypatch.setattr(
        packet.runner,
        "log_matches_condition",
        lambda log, condition, unused_manifest: (
            log.condition_id == condition.condition_id
        ),
    )

    with pytest.raises(ValueError, match="eligible validation frame"):
        packet._validated_frame(
            REPO_ROOT / "evals/manifests/diselect-wave1a-v0.3.json", log_root
        )

    assert captured_route_dirs == [execution_dir / "openrouter-route-capture"]
