from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1]
LAYOUT = '  <script type="module" src="components/layout.js"></script>\n'
BOOT = '  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>\n'

for f in FRONTEND.glob("*.html"):
    text = f.read_text(encoding="utf-8")
    if "components/layout.js" in text:
        continue
    if "<script" in text:
        text = text.replace("<script", LAYOUT + BOOT + "<script", 1)
    else:
        text = text.replace("</body>", LAYOUT + BOOT + "</body>")
    f.write_text(text, encoding="utf-8")
    print("fixed", f.name)
