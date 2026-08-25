"""Exclude historical slugs that OpenRouter now resolves to another identity."""

from pathlib import Path

path = Path("scripts/freeze_ape120_longitudinal.py")
text = path.read_text(encoding="utf-8")


def replace(old: str, new: str, count: int = 1) -> None:
    global text
    actual = text.count(old)
    if actual != count:
        raise RuntimeError(
            f"APE120 alias-fix anchor mismatch: expected {count}, got {actual}: "
            f"{old[:100]!r}"
        )
    text = text.replace(old, new, count)


replace(
    "def build_live_evidence(\n",
    '''class HistoricalCheckpointUnavailable(RuntimeError):
    """The requested historical slug now resolves to another served identity."""

    def __init__(
        self,
        *,
        requested_model: str,
        model_response_id: object,
        endpoint_inventory_id: object,
        catalog_canonical_slug: object,
        model_canonical_slug: object,
    ) -> None:
        self.record = {
            "requested_model": requested_model,
            "model_response_id": model_response_id,
            "endpoint_inventory_id": endpoint_inventory_id,
            "catalog_canonical_slug": catalog_canonical_slug,
            "model_canonical_slug": model_canonical_slug,
        }
        super().__init__(
            f"OpenRouter no longer binds {requested_model} to its own served identity"
        )


def build_live_evidence(
''',
)

replace(
    '''    if model_record.get("id") != model_id or endpoint_inventory.get("id") != model_id:
        raise RuntimeError(f"OpenRouter model identity changed for {model_id}")
    canonical_slug = model_record.get("canonical_slug")
    if (
        not isinstance(canonical_slug, str)
        or models_record.get("canonical_slug") != canonical_slug
    ):
        raise RuntimeError(f"OpenRouter canonical identity is inconsistent for {model_id}")
''',
    '''    canonical_slug = model_record.get("canonical_slug")
    if (
        model_record.get("id") != model_id
        or endpoint_inventory.get("id") != model_id
        or not isinstance(canonical_slug, str)
        or models_record.get("canonical_slug") != canonical_slug
    ):
        raise HistoricalCheckpointUnavailable(
            requested_model=model_id,
            model_response_id=model_record.get("id"),
            endpoint_inventory_id=endpoint_inventory.get("id"),
            catalog_canonical_slug=models_record.get("canonical_slug"),
            model_canonical_slug=canonical_slug,
        )
''',
)

replace(
    '''    conditions: list[dict[str, Any]] = []
    selection_records: list[dict[str, Any]] = []
    captures: dict[str, tuple[bytes, dict[str, Any], bytes, dict[str, Any]]] = {}
''',
    '''    conditions: list[dict[str, Any]] = []
    selection_records: list[dict[str, Any]] = []
    included_rows: list[dict[str, Any]] = []
    identity_alias_exclusions: list[dict[str, Any]] = []
    captures: dict[str, tuple[bytes, dict[str, Any], bytes, dict[str, Any]]] = {}
''',
)

replace(
    '''        evidence, prices, _ = build_live_evidence(
            model_id=model_id,
            provider_tag=row["provider_tag"],
            observed_at=observed_at,
            models_raw=models_raw,
            models_payload=models_payload,
            zdr_raw=zdr_raw,
            zdr_payload=zdr_payload,
            model_raw=model_raw,
            model_payload=model_payload,
            endpoints_raw=endpoints_raw,
            endpoints_payload=endpoints_payload,
            required_max_tokens=TARGET_MAX_TOKENS,
        )
        base_id = safe_id(f"ape120-{model_id}-{evidence['provider_tag']}")
''',
    '''        try:
            evidence, prices, _ = build_live_evidence(
                model_id=model_id,
                provider_tag=row["provider_tag"],
                observed_at=observed_at,
                models_raw=models_raw,
                models_payload=models_payload,
                zdr_raw=zdr_raw,
                zdr_payload=zdr_payload,
                model_raw=model_raw,
                model_payload=model_payload,
                endpoints_raw=endpoints_raw,
                endpoints_payload=endpoints_payload,
                required_max_tokens=TARGET_MAX_TOKENS,
            )
        except HistoricalCheckpointUnavailable as exc:
            identity_alias_exclusions.append(
                {
                    "model_id": model_id,
                    "release_date": row.get("release_date"),
                    "family": row.get("family"),
                    "selection_basis": row.get("selection_basis"),
                    "reason": (
                        "requested historical slug resolves to another currently "
                        "served OpenRouter identity"
                    ),
                    **exc.record,
                }
            )
            continue
        included_rows.append(row)
        base_id = safe_id(f"ape120-{model_id}-{evidence['provider_tag']}")
''',
)

replace(
    "    helper_model = exact_record(\n",
    '''    expected_target_cost = sum(estimate_target_cost(row) for row in included_rows)
    if not conditions:
        raise RuntimeError("no historically bound APE-120 conditions remain")

    helper_model = exact_record(
''',
)

replace(
    '''        "open_weight_condition_count": sum(
            row.get("selection_basis") == "open_weight_total_params_ge_100b"
            for row in selected_rows
        ),
        "hosted_condition_count": len(CURATED_HOSTED_CHECKPOINTS),
''',
    '''        "open_weight_condition_count": sum(
            row.get("selection_basis") == "open_weight_total_params_ge_100b"
            for row in included_rows
        ),
        "hosted_condition_count": sum(
            row.get("selection_basis") != "open_weight_total_params_ge_100b"
            for row in included_rows
        ),
        "identity_alias_exclusion_count": len(identity_alias_exclusions),
        "identity_alias_exclusions": identity_alias_exclusions,
''',
)

replace(
    '''            "exclusions": "mutable aliases, small/specialist tiers, premium duplicate tiers, multi-agent variants, and checkpoints that cannot fit the fixed USD 30 key cap",
''',
    '''            "exclusions": (
                "mutable or remapped aliases, small/specialist tiers, premium "
                "duplicate tiers, multi-agent variants, and checkpoints that cannot "
                "fit the fixed USD 30 key cap"
            ),
''',
)

replace(
    '''                "hosted_count": selection["hosted_condition_count"],
                "expected_target_cost_usd": expected_target_cost,
''',
    '''                "hosted_count": selection["hosted_condition_count"],
                "identity_alias_exclusion_count": selection[
                    "identity_alias_exclusion_count"
                ],
                "expected_target_cost_usd": expected_target_cost,
''',
)

path.write_text(text, encoding="utf-8")
