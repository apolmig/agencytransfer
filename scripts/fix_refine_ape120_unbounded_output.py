"""Treat a null endpoint output ceiling as unbounded rather than unsupported."""

from pathlib import Path

path = Path("scripts/refine_ape120_inventory_v03.py")
text = path.read_text(encoding="utf-8")
old = '''        if (
            isinstance(max_completion, bool)
            or not isinstance(max_completion, int)
            or max_completion < TARGET_MAX_OUTPUT_TOKENS
        ):
            continue
'''
new = '''        if max_completion is not None and (
            isinstance(max_completion, bool)
            or not isinstance(max_completion, int)
            or max_completion < TARGET_MAX_OUTPUT_TOKENS
        ):
            continue
'''
if text.count(old) != 1:
    raise RuntimeError(f"unexpected output-ceiling anchor count: {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
