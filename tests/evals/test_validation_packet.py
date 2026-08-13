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
    manifest = load_manifest(REPO_ROOT / "evals/manifests/diselect-wave1a-v0.2.json")
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
        manifest_path=REPO_ROOT / "evals/manifests/diselect-wave1a-v0.2.json",
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
            manifest_path=REPO_ROOT / "evals/manifests/diselect-wave1a-v0.2.json",
            log_dir=tmp_path / "logs",
            key_file=_key(tmp_path / "key-a"),
            output_dir=existing,
            reviewer_pseudonyms=["reviewer-a", "reviewer-b"],
        )

    with pytest.raises(ValueError, match="owner-only"):
        packet.create_validation_packets(
            manifest_path=REPO_ROOT / "evals/manifests/diselect-wave1a-v0.2.json",
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
