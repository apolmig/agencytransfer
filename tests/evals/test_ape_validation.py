from __future__ import annotations

import hashlib
import json
import stat
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import atb_eval.ape_adjudication_packet as adjudication
import atb_eval.ape_validation_evidence as evidence
import atb_eval.ape_validation_packet as packet
import pytest
from atb_eval.manifest import load_manifest

REPO_ROOT = Path(__file__).resolve().parents[2]
CATEGORIES = (
    "Conspiracy",
    "BenignOpinion",
    "BenignFactual",
    "Controversial",
    "NoncontroversiallyHarmful",
    "UnderminingControl",
)


def _key(path: Path) -> Path:
    path.write_bytes(bytes(range(32)))
    path.chmod(0o600)
    return path


def _frame(*, automated_missing_in_stratum: int = 0) -> packet.ExecutionFrame:
    manifest = load_manifest(REPO_ROOT / "evals/manifests/ape-stage2a-v0.1.json")
    items: list[packet.FrameItem] = []
    index = 0
    for condition in ("anchor-a", "anchor-b", "anchor-c"):
        for category in CATEGORIES:
            for offset in range(20):
                index += 1
                automated_class = ("attempt", "refusal", "non_persuasive")[offset % 3]
                if (
                    offset < automated_missing_in_stratum
                    and condition == "anchor-a"
                    and category == "Conspiracy"
                ):
                    automated_class = None
                items.append(
                    packet.FrameItem(
                        condition_id=condition,
                        sample_id=f"ape-{index:03d}",
                        epoch=1,
                        stratum=(condition, category),
                        request=(
                            f"Statement:\nFixture {index}\n\n"
                            "Assigned direction:\nsupport\n\n"
                            f"Simulated interlocutor:\nUtterance {index}"
                        ),
                        response=f"Target response {index}",
                        automated_class=automated_class,
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


def _packets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    frame: packet.ExecutionFrame | None = None,
) -> tuple[Path, Path]:
    monkeypatch.setattr(
        packet, "_validated_ape_frame", lambda *unused: frame or _frame()
    )
    monkeypatch.setattr(packet, "verify_committed_file", lambda *unused: None)
    monkeypatch.setattr(packet, "_require_clean_validation_checkout", lambda *unused: None)
    monkeypatch.setattr(evidence, "_require_clean_validation_checkout", lambda *unused: None)
    monkeypatch.setattr(
        adjudication, "_require_clean_validation_checkout", lambda *unused: None
    )
    key = _key(tmp_path / "ape-hmac.key")
    output = tmp_path / "ape-packets"
    packet.create_ape_validation_packets(
        manifest_path=REPO_ROOT / "evals/manifests/ape-stage2a-v0.1.json",
        log_dir=tmp_path / "logs",
        key_file=key,
        output_dir=output,
        reviewer_pseudonyms=["reviewer-a", "reviewer-b"],
    )
    return output, key


def test_ape_validation_requires_exact_clean_execution_checkout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        packet.runner,
        "repository_provenance",
        lambda *unused: {"code_commit": "a" * 40, "code_dirty": False},
    )
    packet._require_clean_validation_checkout("a" * 40)
    with pytest.raises(ValueError, match="clean checkout"):
        packet._require_clean_validation_checkout("b" * 40)

    monkeypatch.setattr(
        packet.runner,
        "repository_provenance",
        lambda *unused: {"code_commit": "a" * 40, "code_dirty": True},
    )
    with pytest.raises(ValueError, match="clean checkout"):
        packet._require_clean_validation_checkout("a" * 40)


def _complete(
    path: Path,
    *,
    default: str = "attempt",
    overrides: dict[str, str] | None = None,
) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    value["independent_read_attested"] = True
    for item in value["items"]:
        item["human_label"] = (overrides or {}).get(item["review_item_id"], default)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)
    return value


def _complete_from_private(path: Path, private: dict, *, unscored_id: str | None = None) -> dict:
    labels = {
        item["review_item_id"]: item["automated_class"] or "attempt"
        for item in private["items"]
    }
    if unscored_id is not None:
        labels[unscored_id] = "unscored"
    return _complete(path, overrides=labels)


def test_ape_review_material_includes_direction_and_real_utterance() -> None:
    sample = SimpleNamespace(
        input="The proposition",
        metadata={"direction": "against"},
        messages=[
            {"role": "user", "content": "The proposition"},
            {"role": "user", "content": "I currently support it."},
            {"role": "assistant", "content": "Consider reasons to oppose it."},
        ],
        output=SimpleNamespace(completion="Consider reasons to oppose it."),
        attachments=None,
    )
    request, response = packet._ape_review_material(sample)
    assert "Assigned direction:\noppose" in request
    assert "Simulated interlocutor:\nI currently support it." in request
    assert response == "Consider reasons to oppose it."


def test_ape_packet_is_stratified_blind_and_schema_discriminated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, _key_path = _packets(tmp_path, monkeypatch)
    first = json.loads((output / "reviewer-a.json").read_text(encoding="utf-8"))
    second = json.loads((output / "reviewer-b.json").read_text(encoding="utf-8"))
    private = packet.APEPrivateMap.model_validate_json(
        (output / "private-map.json").read_text(encoding="utf-8")
    )

    assert first["schema_version"] == "atb-ape-validation-review-packet-v0.2"
    assert first["task_kind"] == "ape"
    assert first["label_set_id"] == packet.APE_LABEL_SET_ID
    assert private.item_count == 90
    assert {item.inclusion_probability for item in private.items} == {0.25}
    stratum_by_sample = {row.sample_id: row.stratum for row in _frame().items}
    assert len(
        {
            (item.condition_id, stratum_by_sample[item.sample_id][1])
            for item in private.items
        }
    ) == 18
    assert [item["review_item_id"] for item in first["items"]] != [
        item["review_item_id"] for item in second["items"]
    ]
    rendered = json.dumps(first)
    assert "condition_id" not in rendered
    assert "automated_score" in rendered
    assert all(item["human_label"] is None for item in first["items"])
    assert stat.S_IMODE(output.stat().st_mode) == 0o700
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in output.iterdir())


def test_ape_evidence_preserves_unscored_rows_outside_behavioural_oracle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, key = _packets(tmp_path, monkeypatch)
    private = json.loads((output / "private-map.json").read_text(encoding="utf-8"))
    unscored_id = private["items"][0]["review_item_id"]
    _complete_from_private(output / "reviewer-a.json", private, unscored_id=unscored_id)
    _complete_from_private(output / "reviewer-b.json", private, unscored_id=unscored_id)

    result = evidence.build_ape_validation_evidence(
        reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
        private_map_path=output / "private-map.json",
        key_file=key,
        output_file=output / "evidence.json",
    )
    assert result.probability_sample_n == 90
    assert result.scored_n == 89
    assert result.unscored_n == 1
    assert result.validation_projection == "attempt_vs_rest"
    assert result.macro_f1 == 1.0
    assert result.critical_f1 == 1.0
    assert result.validation_gate_status == "failed"
    assert result.validation_gate_failures == [
        "condition/category joint usable rate is below the frozen threshold"
    ]
    row = next(
        item
        for item in result.rows
        if {label.human_label for label in item.independent_labels} == {"unscored"}
    )
    assert row.review_status == "unscored"
    assert row.oracle_class is None
    assert row.inclusion_probability > 0


def test_ape_automated_unscored_is_excluded_from_f1_but_fails_coverage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, key = _packets(
        tmp_path,
        monkeypatch,
        frame=_frame(automated_missing_in_stratum=20),
    )
    private = json.loads((output / "private-map.json").read_text(encoding="utf-8"))
    _complete_from_private(output / "reviewer-a.json", private)
    _complete_from_private(output / "reviewer-b.json", private)

    result = evidence.build_ape_validation_evidence(
        reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
        private_map_path=output / "private-map.json",
        key_file=key,
        output_file=output / "missing-auto-evidence.json",
    )
    assert result.scored_n == 90
    assert result.unscored_n == 0
    assert result.joint_usable_rate == pytest.approx(85 / 90)
    assert result.macro_f1 == 1.0
    assert result.critical_f1 == 1.0
    assert result.validation_gate_status == "failed"
    assert result.validation_gate_failures == [
        "condition/category joint usable rate is below the frozen threshold"
    ]


def test_ape_stratum_missingness_fails_even_when_global_coverage_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, key = _packets(
        tmp_path,
        monkeypatch,
        frame=_frame(automated_missing_in_stratum=1),
    )
    private = json.loads((output / "private-map.json").read_text(encoding="utf-8"))
    _complete_from_private(output / "reviewer-a.json", private)
    _complete_from_private(output / "reviewer-b.json", private)

    result = evidence.build_ape_validation_evidence(
        reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
        private_map_path=output / "private-map.json",
        key_file=key,
        output_file=output / "concentrated-missing-evidence.json",
    )
    assert result.joint_usable_rate == pytest.approx(89 / 90)
    affected = next(
        item
        for item in result.stratum_coverage
        if item.condition_id == "anchor-a" and item.category == "Conspiracy"
    )
    assert affected.joint_usable_rate == pytest.approx(0.8)
    assert result.validation_gate_status == "failed"
    assert result.validation_gate_failures == [
        "condition/category joint usable rate is below the frozen threshold"
    ]


def test_ape_disagreement_requires_bound_third_reviewer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, key = _packets(tmp_path, monkeypatch)
    first = _complete(output / "reviewer-a.json")
    disputed_id = first["items"][0]["review_item_id"]
    _complete(output / "reviewer-b.json", overrides={disputed_id: "refusal"})
    with pytest.raises(ValueError, match="require independent adjudication"):
        evidence.build_ape_validation_evidence(
            reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
            private_map_path=output / "private-map.json",
            key_file=key,
            output_file=output / "missing.json",
        )

    private_path = output / "private-map.json"
    private = json.loads(private_path.read_text(encoding="utf-8"))
    mapped = next(item for item in private["items"] if item["review_item_id"] == disputed_id)
    adjudications = output / "adjudications.json"
    adjudication.create_ape_adjudication_packet(
        reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
        private_map_path=private_path,
        key_file=key,
        output_file=adjudications,
        adjudicator_pseudonym="reviewer-c",
    )
    completed = json.loads(adjudications.read_text(encoding="utf-8"))
    completed["independent_read_attested"] = True
    completed["items"][0]["human_label"] = "refusal"
    adjudications.write_text(
        json.dumps(completed, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    adjudications.chmod(0o600)
    result = evidence.build_ape_validation_evidence(
        reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
        private_map_path=output / "private-map.json",
        key_file=key,
        adjudication_packet_path=adjudications,
        output_file=output / "adjudicated.json",
    )
    row = next(item for item in result.rows if item.sample_id == mapped["sample_id"])
    assert row.adjudication_status == "adjudicated"
    assert row.oracle_class == "refusal"
    assert row.adjudicator_pseudonym == "reviewer-c"


def test_ape_evidence_rejects_rehashed_adjudication_material_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, key = _packets(tmp_path, monkeypatch)
    first = _complete(output / "reviewer-a.json")
    disputed_id = first["items"][0]["review_item_id"]
    _complete(output / "reviewer-b.json", overrides={disputed_id: "refusal"})
    private_path = output / "private-map.json"
    adjudications = output / "adjudications.json"
    adjudication.create_ape_adjudication_packet(
        reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
        private_map_path=private_path,
        key_file=key,
        output_file=adjudications,
        adjudicator_pseudonym="reviewer-c",
    )
    completed = json.loads(adjudications.read_text(encoding="utf-8"))
    completed["independent_read_attested"] = True
    completed["items"][0]["request"] = "Substituted adjudication request"
    completed["items"][0]["request_sha256"] = hashlib.sha256(
        completed["items"][0]["request"].encode()
    ).hexdigest()
    completed["items"][0]["human_label"] = "refusal"
    adjudications.write_text(
        json.dumps(completed, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    adjudications.chmod(0o600)

    with pytest.raises(ValueError, match="content binding"):
        evidence.build_ape_validation_evidence(
            reviewer_packet_paths=(
                output / "reviewer-a.json",
                output / "reviewer-b.json",
            ),
            private_map_path=private_path,
            key_file=key,
            adjudication_packet_path=adjudications,
            output_file=output / "tampered-adjudication-evidence.json",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [("label_set_id", "atb-diselect-labels-v0.1"), ("codebook_version", "wrong")],
)
def test_ape_packet_rejects_cross_construct_discriminators(
    field: str,
    value: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output, key = _packets(tmp_path, monkeypatch)
    _complete(output / "reviewer-a.json")
    second = _complete(output / "reviewer-b.json")
    second[field] = value
    (output / "reviewer-b.json").write_text(
        json.dumps(second, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "reviewer-b.json").chmod(0o600)
    with pytest.raises(ValueError, match="invalid"):
        evidence.build_ape_validation_evidence(
            reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
            private_map_path=output / "private-map.json",
            key_file=key,
            output_file=output / "invalid.json",
        )


def test_ape_packet_rejects_content_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, key = _packets(tmp_path, monkeypatch)
    _complete(output / "reviewer-a.json")
    second = _complete(output / "reviewer-b.json")
    second["items"][0]["response"] = "tampered"
    (output / "reviewer-b.json").write_text(
        json.dumps(second, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "reviewer-b.json").chmod(0o600)
    with pytest.raises(ValueError, match="content binding"):
        evidence.build_ape_validation_evidence(
            reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
            private_map_path=output / "private-map.json",
            key_file=key,
            output_file=output / "tampered.json",
        )


@pytest.mark.parametrize(
    ("field", "mutator"),
    [
        ("protocol_id", lambda value: value + "-tampered"),
        ("codebook_sha256", lambda _value: "f" * 64),
        ("reviewer_pseudonyms", lambda value: [value[0], "reviewer-c"]),
    ],
)
def test_ape_private_map_rejects_header_tampering(
    field: str,
    mutator: Callable[[object], object],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output, key = _packets(tmp_path, monkeypatch)
    _complete(output / "reviewer-a.json")
    _complete(output / "reviewer-b.json")
    private_path = output / "private-map.json"
    private = json.loads(private_path.read_text(encoding="utf-8"))
    private[field] = mutator(private[field])
    private_path.write_text(
        json.dumps(private, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    private_path.chmod(0o600)
    with pytest.raises(ValueError, match=r"packet-set binding|codebook copy"):
        evidence.build_ape_validation_evidence(
            reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
            private_map_path=private_path,
            key_file=key,
            output_file=output / "header-tampered.json",
        )


def test_ape_private_map_rejects_automated_class_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, key = _packets(tmp_path, monkeypatch)
    _complete(output / "reviewer-a.json")
    _complete(output / "reviewer-b.json")
    private_path = output / "private-map.json"
    private = json.loads(private_path.read_text(encoding="utf-8"))
    original = private["items"][0]["automated_class"]
    private["items"][0]["automated_class"] = (
        "refusal" if original != "refusal" else "attempt"
    )
    private_path.write_text(
        json.dumps(private, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    private_path.chmod(0o600)
    with pytest.raises(ValueError, match="packet-set binding"):
        evidence.build_ape_validation_evidence(
            reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
            private_map_path=private_path,
            key_file=key,
            output_file=output / "class-tampered.json",
        )


def test_ape_private_map_rejects_category_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, key = _packets(tmp_path, monkeypatch)
    _complete(output / "reviewer-a.json")
    _complete(output / "reviewer-b.json")
    private_path = output / "private-map.json"
    private = json.loads(private_path.read_text(encoding="utf-8"))
    private["items"][0]["category"] = "TamperedCategory"
    private_path.write_text(
        json.dumps(private, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    private_path.chmod(0o600)
    with pytest.raises(ValueError, match="packet-set binding"):
        evidence.build_ape_validation_evidence(
            reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
            private_map_path=private_path,
            key_file=key,
            output_file=output / "category-tampered.json",
        )


def test_ape_evidence_revalidates_the_delivered_codebook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, key = _packets(tmp_path, monkeypatch)
    _complete(output / "reviewer-a.json")
    _complete(output / "reviewer-b.json")
    (output / "codebook.md").write_text("tampered\n", encoding="utf-8")
    (output / "codebook.md").chmod(0o600)
    with pytest.raises(ValueError, match="codebook copy"):
        evidence.build_ape_validation_evidence(
            reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
            private_map_path=output / "private-map.json",
            key_file=key,
            output_file=output / "codebook-tampered.json",
        )


def test_ape_final_evidence_hmac_rejects_coordinated_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, key = _packets(tmp_path, monkeypatch)
    private = json.loads((output / "private-map.json").read_text(encoding="utf-8"))
    _complete_from_private(output / "reviewer-a.json", private)
    _complete_from_private(output / "reviewer-b.json", private)
    evidence_path = output / "evidence.json"
    evidence.build_ape_validation_evidence(
        reviewer_packet_paths=(output / "reviewer-a.json", output / "reviewer-b.json"),
        private_map_path=output / "private-map.json",
        key_file=key,
        output_file=evidence_path,
    )
    assert evidence.load_verified_ape_validation_evidence(evidence_path, key)

    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    payload["protocol_id"] += "-tampered"
    evidence_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    evidence_path.chmod(0o600)
    with pytest.raises(ValueError, match="complete keyed binding"):
        evidence.load_verified_ape_validation_evidence(evidence_path, key)
