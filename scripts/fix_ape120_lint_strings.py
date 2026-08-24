"""One-shot wrapping of descriptive strings before the frozen APE120 commit."""

from pathlib import Path


def replace(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"unexpected wrapping anchor count in {path}: {text.count(old)}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace(
    "evals/atb_eval/manifest.py",
    '                        "belief range, paired interlocutor, bounded sampling contract, and one epoch"',
    '                        "belief range, paired interlocutor, bounded sampling contract, "\n'
    '                        "and one epoch"',
)
replace(
    "scripts/build_ape120_inventory.py",
    '            "hosted": "stable general GPT/o-series, Claude except Haiku/Fast, Gemini except Lite/Nano, and Grok except small/code tiers",',
    '            "hosted": (\n'
    '                "stable general GPT/o-series, Claude except Haiku/Fast, "\n'
    '                "Gemini except Lite/Nano, and Grok except small/code tiers"\n'
    '            ),',
)
replace(
    "scripts/build_ape120_inventory.py",
    '            "open_weight": "live OpenRouter text model with Hugging Face identity and documented total parameters >=100B",',
    '            "open_weight": (\n'
    '                "live OpenRouter text model with Hugging Face identity and "\n'
    '                "documented total parameters >=100B"\n'
    '            ),',
)
replace(
    "scripts/build_ape120_inventory.py",
    '            "route": "one fixed operational endpoint, preferring ZDR, no fallback, request price zero, no relevant conditional override, and >=1024 output tokens",',
    '            "route": (\n'
    '                "one fixed operational endpoint, preferring ZDR, no fallback, "\n'
    '                "request price zero, no relevant conditional override, and "\n'
    '                ">=1024 output tokens"\n'
    '            ),',
)
replace(
    "scripts/build_ape120_inventory.py",
    '            "budget": "all eligible open weights >=100B plus a preregistered hosted timeline spanning the oldest live and major subsequent checkpoints",',
    '            "budget": (\n'
    '                "all eligible open weights >=100B plus a preregistered hosted "\n'
    '                "timeline spanning the oldest live and major subsequent checkpoints"\n'
    '            ),',
)
replace(
    "scripts/freeze_ape120_longitudinal.py",
    '            "open_weight": "all live general text checkpoints with documented total parameters >=100B",',
    '            "open_weight": (\n'
    '                "all live general text checkpoints with documented total "\n'
    '                "parameters >=100B"\n'
    '            ),',
)
replace(
    "scripts/freeze_ape120_longitudinal.py",
    '            "hosted": "preregistered major GPT, Claude Sonnet, Gemini, and Grok checkpoints spanning the oldest live and subsequent releases inside the target allowance",',
    '            "hosted": (\n'
    '                "preregistered major GPT, Claude Sonnet, Gemini, and Grok "\n'
    '                "checkpoints spanning the oldest live and subsequent releases "\n'
    '                "inside the target allowance"\n'
    '            ),',
)
replace(
    "scripts/freeze_ape120_longitudinal.py",
    '            "exclusions": "mutable aliases, small/specialist tiers, premium duplicate tiers, multi-agent variants, and checkpoints that cannot fit the fixed USD 30 key cap",',
    '            "exclusions": (\n'
    '                "mutable aliases, small/specialist tiers, premium duplicate "\n'
    '                "tiers, multi-agent variants, and checkpoints that cannot fit "\n'
    '                "the fixed USD 30 key cap"\n'
    '            ),',
)
