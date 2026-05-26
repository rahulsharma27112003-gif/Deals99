import re
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1]
BOOT = '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>'

for f in FRONTEND.glob("*.html"):
    text = f.read_text(encoding="utf-8")
    count = text.count(BOOT)
    if count <= 1:
        continue
  # keep first bootstrap after layout.js block
    parts = text.split(BOOT)
    text = parts[0] + BOOT + "".join(parts[1:])
    f.write_text(text, encoding="utf-8")
    print("deduped", f.name, count, "-> 1")
