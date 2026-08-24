"""Force LF output so the generated inventory passes repository checks."""

from pathlib import Path

path = Path("scripts/build_ape120_inventory.py")
text = path.read_text(encoding="utf-8")
old = 'writer = csv.DictWriter(handle, fieldnames=fieldnames)'
new = 'writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\\n")'
if text.count(old) != 1:
    raise RuntimeError(f"unexpected DictWriter anchor count: {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
