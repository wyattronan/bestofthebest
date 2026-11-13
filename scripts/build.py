#!/usr/bin/env python3
"""Assemble data/cities/*.json into the CITIES_DATA blob inside index.html.

index.html is the single, self-contained, deployed artifact. Its data is
*build-managed*: the `const CITIES_DATA={...}` object is replaced from the
per-city JSON files. Everything else in index.html (layout, styles, scripts,
embedded fonts/images/video) is hand-authored and left untouched.

Usage: python3 scripts/build.py   (run from repo root)
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
HTML = ROOT / "index.html"
CITY_DIR = ROOT / "data" / "cities"

def load_cities():
    order = json.loads((CITY_DIR / "_order.json").read_text())["order"]
    data = {}
    for city in order:
        data[city] = json.loads((CITY_DIR / f"{city}.json").read_text(encoding="utf-8"))
    return data

def find_blob(s):
    m = re.search(r"const CITIES_DATA=", s)
    if not m:
        sys.exit("ERROR: `const CITIES_DATA=` not found in index.html")
    st = s.index("{", m.end())
    depth = 0; i = st
    while i < len(s):
        c = s[i]
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: break
        i += 1
    return st, i + 1

def main():
    s = HTML.read_text(encoding="utf-8")
    st, en = find_blob(s)
    blob = json.dumps(load_cities(), ensure_ascii=False, separators=(",", ":"))
    new = s[:st] + blob + s[en:]
    if new == s:
        print("index.html already up to date.")
        return
    HTML.write_text(new, encoding="utf-8")
    print(f"index.html rebuilt ({len(new):,} bytes).")

if __name__ == "__main__":
    main()
