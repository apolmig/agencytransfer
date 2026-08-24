"""Correct the one stale formatting anchor in the v0.3 one-shot migration."""

from pathlib import Path

path = Path("scripts/refine_ape120_inventory_v03.py")
text = path.read_text(encoding="utf-8")
old = '''        open_weight_eligible = bool(open_weight and total_b is not None and total_b >= 100)
        candidate = hosted or open_weight_eligible
'''
new = '''        open_weight_eligible = bool(
            open_weight and total_b is not None and total_b >= 100
        )
        candidate = hosted or open_weight_eligible
'''
if text.count(old) != 1:
    raise RuntimeError(f"unexpected stale-anchor count: {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
