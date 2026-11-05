"""Bygger en statisk sajt (dist/index.html) med färsk data inbäddad.
Körs automatiskt av GitHub Actions, men fungerar även lokalt: python build.py"""
import datetime
import json
from pathlib import Path

from app import PAYLOAD  # hämtar och bearbetar datan

root = Path(__file__).parent
html = (root / "templates" / "index.html").read_text(encoding="utf-8")

old = 'D = await (await fetch("/api/data")).json();'
assert old in html, "Hittade inte raden som hämtar data i index.html"
html = html.replace(old, "D = window.__DATA__;")

stamp = datetime.date.today().isoformat()
html = html.replace("<footer>Källa:", f"<footer>Sidan byggdes {stamp}. Källa:", 1)
data = json.dumps(PAYLOAD, separators=(",", ":"), ensure_ascii=False)
html = html.replace("</head>", f"<script>window.__DATA__={data};</script>\n</head>", 1)

out = root / "dist"
out.mkdir(exist_ok=True)
(out / "index.html").write_text(html, encoding="utf-8")
(out / ".nojekyll").write_text("")
print(f"Klart: {out / 'index.html'} ({len(html) / 1e6:.2f} MB), data t.o.m. {PAYLOAD['last']}")
