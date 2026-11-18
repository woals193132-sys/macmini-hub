#!/usr/bin/env python3
"""Build hub.html: index.html + data.json inlined as a single standalone file.

Usage: python3 build.py
Writes hub.html next to this script.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
index_html = (HERE / "index.html").read_text(encoding="utf-8")
data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))

payload = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
anchor = "<script>\n(function(){"
if anchor not in index_html:
    raise SystemExit("anchor not found in index.html")

inline = "<script>window.__INLINE_DATA__ = " + payload + ";\n</script>\n"
out = index_html.replace(anchor, inline + anchor, 1)
(HERE / "hub.html").write_text(out, encoding="utf-8")
print("hub.html written:", len(out), "chars")
