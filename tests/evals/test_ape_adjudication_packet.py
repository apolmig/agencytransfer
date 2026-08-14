from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path

import atb_eval.ape_adjudication_packet as adjudication
import pytest
from atb_eval.ape_validation_packet import (
    APEPrivateMap,
    APEPrivateMapItem,
    APEReviewPacket,
    APEReviewPacketItem,
    _ape_packet_set_id,
)
from atb_eval.validation_packet import (
    BLINDED_FIELDS,
    _domain_hmac,
    _key_confirmation_hmac,
    _response_hmac,
)


@pytest.fixture(autouse=True)
def _fixture_checkout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        adjudication, "_require_clean_validation_checkout", lambda *unused: None
    )


def _write_private(path: Path, value: object) -> Path:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")  # type: ignore[union-attr]
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)
    return path


def _inputs(
    tmp_path: Path, *, disagreements: bool = True
) -> tuple[tuple[Path, Path], Path, Path, APEPrivateMap, tuple[str, ...]]:
    tmp_path.chmod(0o700)
    key_bytes = bytes(range(32))
    key_path = tmp_path / "ape.key"
    key_path.write_bytes(key_bytes)
    key_path.chmod(0o600)
    codebook_bytes = b"APE fixture codebook\n"
    codebook_sha256 = hashlib.sha256(codebook_bytes).hexdigest()
    codebook_path = tmp_path / "codebook.md"
    codebook_path.write_bytes(codebook_bytes)
    codebook_path.chmod(0o600)

    materials = [
        ("condition-hidden-a", "sample-hidden-1", "Request one", "Response one", "attempt"),
        ("condition-hidden-b", "sample-hidden-2", "Request two", "Response two", "refusal"),
        (
            "condition-hidden-c",
            "sample-hidden-3",
            "Request three",
            "Response three",
            "non_persuasive",
        ),
    ]
    descriptors = [
        {
            "condition_id": condition_id,
            "category": "Controversial",
            "sample_id": sample_id,
            "epoch": 1,
            "inclusion_probability": 0.5,
            "request_sha256": hashlib.sha256(request.encode()).hexdigest(),
            "response_sha256": hashlib.sha256(response.encode()).hexdigest(),
            "automated_class": automated_class,
        }
        for condition_id, sample_id, request, response, automated_class in materials
    ]
    packet_set_id = _ape_packet_set_id(
        key_bytes,
        protocol_id="ape-test-v0.2",
        manifest_sha256="a" * 64,
        execution_id="1" * 32,
        code_commit="b" * 40,
        evidence_inventory_sha256="c" * 64,
        codebook_sha256=codebook_sha256,
        reviewer_pseudonyms=["reviewer-a", "reviewer-b"],
        macro_f1_min=0.8,
        critical_f1_min=0.75,
        minimum_joint_usable_rate=0.95,
        sample_descriptors=descriptors,
    )

    private_items: list[APEPrivateMapItem] = []
    review_items: list[APEReviewPacketItem] = []
    review_ids: list[str] = []
    for descriptor, material in zip(descriptors, materials, strict=True):
        condition_id, sample_id, request, response, _automated_class = material
        review_item_id = _domain_hmac(
            key_bytes,
            "atb-ape-validation-review-item-v0.2",
            {
                "packet_set_id": packet_set_id,
                "response_key": [condition_id, sample_id, 1],
            },
        )
        review_ids.append(review_item_id)
        response_hmac = _response_hmac(
            key_bytes,
            packet_set_id=packet_set_id,
            review_item_id=review_item_id,
            condition_id=condition_id,
            sample_id=sample_id,
            epoch=1,
            inclusion_probability=0.5,
            request_sha256=descriptor["request_sha256"],
            response_sha256=descriptor["response_sha256"],
        )
        private_items.append(
            APEPrivateMapItem(
                review_item_id=review_item_id,
                response_hmac=response_hmac,
                condition_id=condition_id,
                category="Controversial",
                sample_id=sample_id,
                epoch=1,
                inclusion_probability=0.5,
                request_sha256=descriptor["request_sha256"],
                response_sha256=descriptor["response_sha256"],
                automated_class=descriptor["automated_class"],
            )
        )
        review_items.append(
            APEReviewPacketItem(
                review_item_id=review_item_id,
                response_hmac=response_hmac,
                request_sha256=descriptor["request_sha256"],
                response_sha256=descriptor["response_sha256"],
                inclusion_probability=0.5,
                request=request,
                response=response,
                human_label=None,
            )
        )

    private_map = APEPrivateMap(
        schema_version="atb-ape-validation-private-map-v0.2",
        task_kind="ape",
        label_set_id="atb-ape-attempt-labels-v0.1",
        validation_projection="attempt_vs_rest",
        packet_set_id=packet_set_id,
        protocol_id="ape-test-v0.2",
        manifest_sha256="a" * 64,
        execution_id="1" * 32,
        code_commit="b" * 40,
        evidence_inventory_sha256="c" * 64,
        codebook_version="atb-ape-attempt-v0.1",
        codebook_sha256=codebook_sha256,
        macro_f1_min=0.8,
        critical_class="attempt",
        critical_f1_min=0.75,
        minimum_joint_usable_rate=0.95,
        reviewer_pseudonyms=["reviewer-a", "reviewer-b"],
        key_confirmation_hmac=_key_confirmation_hmac(key_bytes, packet_set_id),
        item_count=len(private_items),
        items=private_items,
    )
    private_path = _write_private(tmp_path / "private-map.json", private_map)
    first_labels = ["attempt", "attempt", "unscored"]
    second_labels = (
        ["attempt", "refusal", "non_persuasive"] if disagreements else first_labels
    )
    packet_paths: list[Path] = []
    for reviewer, labels, items in (
        ("reviewer-a", first_labels, review_items),
        ("reviewer-b", second_labels, list(reversed(review_items))),
    ):
        labels_by_id = dict(zip(review_ids, labels, strict=True))
        completed_items = [
            item.model_copy(update={"human_label": labels_by_id[item.review_item_id]})
            for item in items
        ]
        review_packet = APEReviewPacket(
            schema_version="atb-ape-validation-review-packet-v0.2",
            task_kind="ape",
            label_set_id="atb-ape-attempt-labels-v0.1",
            validation_projection="attempt_vs_rest",
            packet_set_id=packet_set_id,
            protocol_id="ape-test-v0.2",
            codebook_version="atb-ape-attempt-v0.1",
            codebook_sha256=codebook_sha256,
            reviewer_pseudonym=reviewer,
            independent_read_attested=True,
            blinded_fields=list(BLINDED_FIELDS),
            item_count=len(completed_items),
            items=completed_items,
        )
        packet_paths.append(_write_private(tmp_path / f"{reviewer}.json", review_packet))
    return (
        (packet_paths[0], packet_paths[1]),
        private_path,
        key_path,
        private_map,
        tuple(review_ids),
    )


def test_adjudication_packet_is_blind(tmp_path: Path) -> None:
    packet_paths, private_path, key_path, _private_map, _review_ids = _inputs(tmp_path)
    output_path = tmp_path / "reviewer-c.json"
    result = adjudication.create_ape_adjudication_packet(
        reviewer_packet_paths=packet_paths,
        private_map_path=private_path,
        key_file=key_path,
        output_file=output_path,
        adjudicator_pseudonym="reviewer-c",
    )

    assert all(item.human_label is None for item in result.items)
    assert stat.S_IMODE(output_path.stat().st_mode) == 0o600

    raw = json.loads(output_path.read_text(encoding="utf-8"))
    rendered = json.dumps(raw)
    assert "condition_id" not in rendered
    assert "sample_id" not in rendered
    assert "inclusion_probability" not in rendered
    assert "automated_class" not in rendered
    assert "reviewer-a" not in rendered and "reviewer-b" not in rendered
    assert "refusal" not in rendered and "non_persuasive" not in rendered
    assert {"request", "response"} <= set(raw["items"][0])


def test_adjudication_packet_contains_only_disagreements(
    tmp_path: Path,
) -> None:
    packet_paths, private_path, key_path, private_map, review_ids = _inputs(tmp_path)
    output_path = tmp_path / "reviewer-c.json"
    result = adjudication.create_ape_adjudication_packet(
        reviewer_packet_paths=packet_paths,
        private_map_path=private_path,
        key_file=key_path,
        output_file=output_path,
        adjudicator_pseudonym="reviewer-c",
    )

    assert result.packet_set_id == private_map.packet_set_id
    assert result.item_count == 2
    assert {item.review_item_id for item in result.items} == set(review_ids[1:])
    expected_hmacs = {
        item.review_item_id: item.response_hmac for item in private_map.items
    }
    assert all(
        item.response_hmac == expected_hmacs[item.review_item_id] for item in result.items
    )

    raw = json.loads(output_path.read_text(encoding="utf-8"))
    raw["independent_read_attested"] = True
    for item in raw["items"]:
        item["human_label"] = "refusal"
    completed = adjudication.APEAdjudicationReviewPacket.model_validate(raw)
    assert completed.item_count == 2
    assert {item.review_item_id for item in completed.items} == set(review_ids[1:])


def test_adjudication_packet_rejects_tampered_review_material(tmp_path: Path) -> None:
    packet_paths, private_path, key_path, _private_map, _review_ids = _inputs(tmp_path)
    tampered = json.loads(packet_paths[1].read_text(encoding="utf-8"))
    tampered["items"][0]["response"] = "Tampered response"
    _write_private(packet_paths[1], tampered)

    output_path = tmp_path / "must-not-exist.json"
    with pytest.raises(ValueError, match="content binding"):
        adjudication.create_ape_adjudication_packet(
            reviewer_packet_paths=packet_paths,
            private_map_path=private_path,
            key_file=key_path,
            output_file=output_path,
            adjudicator_pseudonym="reviewer-c",
        )
    assert not output_path.exists()


def test_adjudication_packet_rejects_absence_of_disagreements(tmp_path: Path) -> None:
    packet_paths, private_path, key_path, _private_map, _review_ids = _inputs(
        tmp_path, disagreements=False
    )
    output_path = tmp_path / "must-not-exist.json"
    with pytest.raises(ValueError, match="no disagreements"):
        adjudication.create_ape_adjudication_packet(
            reviewer_packet_paths=packet_paths,
            private_map_path=private_path,
            key_file=key_path,
            output_file=output_path,
            adjudicator_pseudonym="reviewer-c",
        )
    assert not output_path.exists()
