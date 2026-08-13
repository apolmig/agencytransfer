from __future__ import annotations

import json
import stat
from pathlib import Path

import atb_eval.validation_evidence as evidence
import atb_eval.validation_packet as packet
import pytest
from atb_eval.manifest import load_manifest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _frame() -> packet.ExecutionFrame:
    manifest = load_manifest(REPO_ROOT / "evals/manifests/diselect-wave1a-v0.3.json")
    items: list[packet.FrameItem] = []
    index = 0
    for condition in manifest.models:
        for use_case in ("voting", "mps", "baseline"):
            for _unused in range(10):
                index += 1
                items.append(
                    packet.FrameItem(
                        condition_id=condition.condition_id,
                        sample_id=f"sample-{index:03d}",
                        epoch=1,
                        stratum=(condition.condition_id, use_case),
                        request=f"Synthetic review request {index}",
                        response=f"Synthetic review response {index}",
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


def _packets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    monkeypatch.setattr(packet, "_validated_frame", lambda *unused: _frame())
    key = tmp_path / "hmac.key"
    key.write_bytes(bytes(range(32)))
    key.chmod(0o600)
    output = tmp_path / "packets"
    packet.create_validation_packets(
        manifest_path=REPO_ROOT / "evals/manifests/diselect-wave1a-v0.3.json",
        log_dir=tmp_path / "logs",
        key_file=key,
        output_dir=output,
        reviewer_pseudonyms=["reviewer-a", "reviewer-b"],
    )
    return output, key


def _complete(
    path: Path, *, default: str = "comply", overrides: dict[str, str] | None = None
) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    value["independent_read_attested"] = True
    for item in value["items"]:
        item["native_class"] = (overrides or {}).get(item["review_item_id"], default)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)
    return value


def test_completed_agreement_packets_produce_owner_only_release_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, key = _packets(tmp_path, monkeypatch)
    _complete(output / "reviewer-a.json")
    _complete(output / "reviewer-b.json")
    target = output / "adjudicated.json"

    result = evidence.build_validation_evidence(
        reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
        private_map_path=output / "private-map.json",
        key_file=key,
        output_file=target,
    )

    assert len(result.rows) == 30
    assert {row.adjudication_status for row in result.rows} == {"agreement"}
    assert {row.oracle_class for row in result.rows} == {"comply"}
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    persisted = json.loads(target.read_text(encoding="utf-8"))
    assert persisted["schema_version"] == "atb-validation-evidence-v0.1"
    rendered = json.dumps(persisted)
    assert "Synthetic review request" not in rendered
    assert "Synthetic review response" not in rendered


def test_disagreement_requires_a_distinct_bound_adjudicator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, key = _packets(tmp_path, monkeypatch)
    first = _complete(output / "reviewer-a.json")
    disputed_id = first["items"][0]["review_item_id"]
    _complete(output / "reviewer-b.json", overrides={disputed_id: "refuse"})

    with pytest.raises(ValueError, match="require independent adjudication"):
        evidence.build_validation_evidence(
            reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
            private_map_path=output / "private-map.json",
            key_file=key,
            output_file=output / "missing-adjudication.json",
        )

    private_map = json.loads((output / "private-map.json").read_text(encoding="utf-8"))
    mapped = next(item for item in private_map["items"] if item["review_item_id"] == disputed_id)
    adjudications = output / "adjudications.json"
    adjudications.write_text(
        json.dumps(
            {
                "schema_version": "atb-validation-adjudications-v0.1",
                "packet_set_id": private_map["packet_set_id"],
                "adjudicator_pseudonym": "reviewer-c",
                "independent_read_attested": True,
                "item_count": 1,
                "items": [
                    {
                        "review_item_id": disputed_id,
                        "response_hmac": mapped["response_hmac"],
                        "native_class": "refuse",
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    adjudications.chmod(0o600)
    result = evidence.build_validation_evidence(
        reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
        private_map_path=output / "private-map.json",
        key_file=key,
        adjudications_path=adjudications,
        output_file=output / "adjudicated.json",
    )
    disputed = next(row for row in result.rows if row.sample_id == mapped["sample_id"])
    assert disputed.adjudication_status == "adjudicated"
    assert disputed.oracle_class == "refuse"
    assert disputed.adjudicator_pseudonym == "reviewer-c"


def test_content_tampering_and_agreed_unscorable_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, key = _packets(tmp_path, monkeypatch)
    first = _complete(output / "reviewer-a.json")
    second = _complete(output / "reviewer-b.json")
    value = json.loads(json.dumps(second))
    value["items"][0]["response"] = "tampered response"
    (output / "reviewer-b.json").write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="content binding"):
        evidence.build_validation_evidence(
            reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
            private_map_path=output / "private-map.json",
            key_file=key,
            output_file=output / "tampered.json",
        )

    agreed_id = first["items"][0]["review_item_id"]
    next(item for item in second["items"] if item["review_item_id"] == agreed_id)[
        "native_class"
    ] = "unscorable"
    (output / "reviewer-b.json").write_text(
        json.dumps(second, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    next(item for item in first["items"] if item["review_item_id"] == agreed_id)["native_class"] = (
        "unscorable"
    )
    (output / "reviewer-a.json").write_text(
        json.dumps(first, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="agreed unscorable"):
        evidence.build_validation_evidence(
            reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
            private_map_path=output / "private-map.json",
            key_file=key,
            output_file=output / "unscorable.json",
        )


def test_evidence_cli_failure_is_content_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail(**unused: object) -> object:
        raise ValueError("private response content")

    monkeypatch.setattr(evidence, "build_validation_evidence", fail)
    status = evidence.main(
        [
            "--reviewer-packet",
            str(tmp_path / "reviewer-a.json"),
            "--reviewer-packet",
            str(tmp_path / "reviewer-b.json"),
            "--private-map",
            str(tmp_path / "private-map.json"),
            "--key-file",
            str(tmp_path / "key"),
            "--output-file",
            str(tmp_path / "evidence.json"),
        ]
    )
    captured = capsys.readouterr()
    assert status == 1
    assert captured.out == ""
    assert captured.err == "validation evidence generation failed safely\n"
    assert "private response" not in captured.err
