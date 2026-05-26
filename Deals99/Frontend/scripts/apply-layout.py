#!/usr/bin/env python3
"""Inject shared header/footer placeholders into all Frontend HTML pages."""
import re
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1]
SKIP = {"components"}

HEAD_ASSETS = """
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="global.css">
"""

LAYOUT_SCRIPT = '  <script type="module" src="components/layout.js"></script>\n'
BOOTSTRAP_SCRIPT = '  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>\n'

NAV_RE = re.compile(
    r"\s*<!--\s*Professional Navbar\s*-->.*?</nav>\s*",
    re.DOTALL | re.IGNORECASE,
)
FOOTER_RE = re.compile(
    r"\s*<!--\s*Professional Footer\s*-->.*?</footer>\s*",
    re.DOTALL | re.IGNORECASE,
)
SIMPLE_NAV_RE = re.compile(
    r"\s*<nav class=\"navbar navbar-expand-lg.*?</nav>\s*",
    re.DOTALL,
)


def active_key(name: str) -> str:
    key = Path(name).stem
    return "home" if key == "index" else key


def ensure_head_assets(html: str) -> str:
    if "bootstrap.min.css" in html and "global.css" in html:
        return html
    if "</head>" not in html:
        return html
    return html.replace("</head>", f"{HEAD_ASSETS}\n</head>", 1)


def strip_old_layout(html: str) -> str:
    html = NAV_RE.sub("\n", html)
    html = FOOTER_RE.sub("\n", html)
    if 'id="site-header"' not in html:
        html = SIMPLE_NAV_RE.sub("\n", html, count=1)
    return html


def insert_placeholders(html: str, key: str) -> str:
    if 'id="site-header"' not in html:
        body_match = re.search(r"<body([^>]*)>", html, re.IGNORECASE)
        if body_match:
            insert = f'\n  <div id="site-header" data-active="{key}"></div>\n  <main class="site-main">\n'
            pos = body_match.end()
            html = html[:pos] + insert + html[pos:]
    if 'id="site-footer"' not in html:
        scripts = list(re.finditer(r"<script", html, re.IGNORECASE))
        if scripts:
            pos = scripts[0].start()
            html = html[:pos] + '  </main>\n  <div id="site-footer"></div>\n' + html[pos:]
        else:
            html = html.replace("</body>", '  </main>\n  <div id="site-footer"></div>\n</body>')
    return html


def close_main_if_needed(html: str) -> str:
    if "<main" in html and "</main>" not in html:
        scripts = list(re.finditer(r"<script", html, re.IGNORECASE))
        if scripts:
            pos = scripts[0].start()
            html = html[:pos] + "  </main>\n" + html[pos:]
    return html


def ensure_scripts(html: str) -> str:
    if "components/layout.js" not in html:
        if BOOTSTRAP_SCRIPT.strip() in html:
            html = html.replace(BOOTSTRAP_SCRIPT, LAYOUT_SCRIPT + BOOTSTRAP_SCRIPT, 1)
        elif "<script" in html:
            html = re.sub(r"(<script)", LAYOUT_SCRIPT + BOOTSTRAP_SCRIPT + r"\1", html, count=1)
        else:
            html = html.replace("</body>", LAYOUT_SCRIPT + BOOTSTRAP_SCRIPT + "</body>")
    if "bootstrap.bundle.min.js" not in html:
        html = html.replace("</body>", BOOTSTRAP_SCRIPT + "</body>")
    return html


def patch_file(path: Path) -> bool:
    html = path.read_text(encoding="utf-8")
    original = html
    html = strip_old_layout(html)
    html = ensure_head_assets(html)
    html = insert_placeholders(html, active_key(path.name))
    html = close_main_if_needed(html)
    html = ensure_scripts(html)
    if html != original:
        path.write_text(html, encoding="utf-8", newline="\n")
        return True
    return False


def main():
    updated = []
    for f in sorted(FRONTEND.glob("*.html")):
        if f.parent.name in SKIP:
            continue
        if patch_file(f):
            updated.append(f.name)
    print("Updated", len(updated), "files:")
    for name in updated:
        print(" ", name)


if __name__ == "__main__":
    main()
