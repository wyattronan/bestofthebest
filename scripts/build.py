#!/usr/bin/env python3
"""Assemble data/cities/*.json (+ data/national.json) into the data blobs inside index.html.

index.html is the single, self-contained, deployed artifact. Its data is
*build-managed*: the `const CITIES_DATA={...}` object is replaced from the
per-city JSON files, and `const USA_DATA={...}` (the USA tab) is computed from
the city files plus data/national.json. Everything else in index.html (layout,
styles, scripts, embedded fonts/images/video) is hand-authored and left untouched.

USA tab, two rankings per kind (restaurants / bars):
  * "count" — every venue that appears on a national (or continental/world)
    list, ranked by how many distinct national lists it's on. Venues in a city
    tab are read from that tab (any list def carrying a `nat` id); national
    entries from cities without a tab come straight from data/national.json.
  * "share" — the 25 venues with the highest share of their own city tab's
    published lists (Wyatt's personal lists are left out of both the count and
    the denominator). Cities with fewer than MIN_POOL published lists sit
    this ranking out, so a 3-for-3 sweep in a small city can't top it.

Usage: python3 scripts/build.py   (run from repo root)
"""
import json, re, sys, pathlib, unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
HTML = ROOT / "index.html"
CITY_DIR = ROOT / "data" / "cities"
NATIONAL = ROOT / "data" / "national.json"
SHARE_TOP = 25
MIN_POOL = 5   # a city tab needs at least this many published lists to compete in the share ranking

def load_cities():
    order = json.loads((CITY_DIR / "_order.json").read_text())["order"]
    data = {}
    for city in order:
        data[city] = json.loads((CITY_DIR / f"{city}.json").read_text(encoding="utf-8"))
    return data

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", " and ").replace("'", "").replace("’", "")
    s = re.sub(r"\b(the|restaurant|bar|and|cocktail|lounge|co|company|kitchen)\b", " ", s)
    return re.sub(r"[^a-z0-9]+", "", s)

def is_personal(key):
    return key.startswith("wyatt")

def build_usa(cities):
    nat = json.loads(NATIONAL.read_text(encoding="utf-8"))
    out = {}
    for kind, pool, lk in (("resto", "restos", "rlists"), ("bars", "bars", "blists")):
        nlists = {k: v for k, v in nat["lists"].items() if v["kind"] == kind}
        rows = []
        # venues with a city tab
        for ck, d in cities.items():
            defs = d[lk]
            for v in d[pool]:
                hits = {}
                for k, rk in v["lists"]:
                    nid = defs.get(k, {}).get("nat")
                    if nid and nid in nlists and nid not in hits:
                        hits[nid] = rk
                if hits:
                    rows.append({"n": v["name"], "ck": ck,
                                 "k": [[a, b] for a, b in hits.items()], "cl": 1 if v.get("cl") else 0})
        # national entries in cities without a tab
        grp = {}
        for e in nat["entries"]:
            if e.get("metro") or nlists.get(e["list"]) is None:
                continue
            key = (norm(e["name"]), e.get("city"), e.get("st"))
            g = grp.setdefault(key, {"n": e["name"], "c": (f'{e["city"]}, {e["st"]}' if e.get("city") else e.get("st") or ""),
                                     "ck": None, "k": [], "cl": 0})
            if not any(x[0] == e["list"] for x in g["k"]):
                g["k"].append([e["list"], e.get("rank")])
        rows += list(grp.values())
        rows.sort(key=lambda r: (-len(r["k"]), r["n"].lower()))
        # share-of-city ranking
        share = []
        for ck, d in cities.items():
            pub = [k for k in d[lk] if not is_personal(k)]
            tot = len(pub)
            if tot < MIN_POOL:
                continue
            for v in d[pool]:
                n = sum(1 for k, _ in v["lists"] if k in pub)
                if n:
                    share.append({"n": v["name"], "ck": ck, "hits": n, "tot": tot,
                                  "pct": round(100 * n / tot, 1), "hood": v.get("hood", ""), "cl": 1 if v.get("cl") else 0})
        share.sort(key=lambda r: (-r["hits"] / r["tot"], -r["hits"], -r["tot"], r["n"].lower()))
        # total-lists ranking: every published list a venue appears on, national + local combined
        total = []
        for ck, d in cities.items():
            defs = d[lk]
            for v in d[pool]:
                pub = [k for k, _ in v["lists"] if not is_personal(k)]
                t = len(set(pub))
                if not t:
                    continue
                nats = {defs[k]["nat"] for k in pub
                        if defs.get(k, {}).get("nat") in nlists}
                total.append({"n": v["name"], "ck": ck, "tot": t, "nat": len(nats),
                              "cl": 1 if v.get("cl") else 0})
        # venues in cities without a tab: their only lists are the national ones
        for g in grp.values():
            total.append({"n": g["n"], "c": g["c"], "ck": None,
                          "tot": len(g["k"]), "nat": len(g["k"]), "cl": g["cl"]})
        total.sort(key=lambda r: (-r["tot"], -r["nat"], r["n"].lower()))
        out[kind] = {
            "lists": {k: {x: v[x] for x in ("name", "year", "mono", "tag", "ranked", "partial") if x in v} for k, v in nlists.items()},
            "count": rows,
            "share": share[:SHARE_TOP],
            "total": total,
            "cities": len(cities),
            "minPool": MIN_POOL,
        }
    return out

def find_blob(s, const):
    m = re.search(r"const " + const + r"=", s)
    if not m:
        sys.exit(f"ERROR: `const {const}=` not found in index.html")
    st = s.index("{", m.end())
    depth = 0; i = st; instr = None
    while i < len(s):
        c = s[i]
        if instr:
            if c == "\\": i += 2; continue
            if c == instr: instr = None
        elif c == '"': instr = c
        elif c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: break
        i += 1
    return st, i + 1

def main():
    s = HTML.read_text(encoding="utf-8")
    cities = load_cities()
    st, en = find_blob(s, "CITIES_DATA")
    new = s[:st] + json.dumps(cities, ensure_ascii=False, separators=(",", ":")) + s[en:]
    if NATIONAL.exists() and "const USA_DATA=" in new:
        usa = build_usa(cities)
        st, en = find_blob(new, "USA_DATA")
        new = new[:st] + json.dumps(usa, ensure_ascii=False, separators=(",", ":")) + new[en:]
    if new == s:
        print("index.html already up to date.")
        return
    HTML.write_text(new, encoding="utf-8")
    print(f"index.html rebuilt ({len(new):,} bytes).")

if __name__ == "__main__":
    main()
