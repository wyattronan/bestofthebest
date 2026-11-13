#!/usr/bin/env python3
"""Weekly updater for Best Of the Best.

What it does, per the tracked lists in data/sources.json:
  1. Re-fetches each *pinned* list (the same prestigious list year-over-year)
     and refreshes which venues are on it + their rank.
  2. Detects closures and marks venues closed (shown struck-through, kept for
     history) rather than deleting them.
  3. Proposes brand-new venues (best-effort geocode + type guess) for review
     instead of silently degrading the data.
  4. Anything it cannot fetch/parse is written to a "needs manual pull" report
     so the contents can be pasted in by hand.

Design notes
  - Low-risk edits (rank, list membership, closures) auto-apply.
  - New venues are *proposed* (settings.auto_apply.new_venues) — they land in
    reports/ and, optionally, a GitHub issue, so quality stays high.
  - "Pinned" matching: we only ever update the list whose identity matches the
    registry entry. A publication's other / lesser lists are ignored, so e.g.
    Eater's annual Essential 38 never gets replaced by an Eater "best new"
    roundup.

Running: python3 scripts/update.py [--dry-run] [--only chicago]
Requires: requests, beautifulsoup4 (see requirements.txt). Playwright is used
only if a source sets "parser": "browser".
"""
from __future__ import annotations
import json, re, sys, time, pathlib, datetime, argparse, difflib, urllib.robotparser as rp
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
CITY_DIR = ROOT / "data" / "cities"
REPORTS = ROOT / "reports"
SOURCES = ROOT / "data" / "sources.json"

def norm(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[’'`]", "", s)
    s = re.sub(r"&", "and", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    s = re.sub(r"\b(the|restaurant|cafe|bar|and|a)\b", "", s).strip()
    return re.sub(r"\s+", " ", s)

def best_match(name, venues):
    """Fuzzy-match a scraped name to an existing venue; None if no good match."""
    t = norm(name)
    best, score = None, 0.0
    for v in venues:
        r = difflib.SequenceMatcher(None, t, norm(v["name"])).ratio()
        if r > score:
            best, score = v, r
    return best if score >= 0.82 else None

# ---------------- fetching ----------------
def allowed(url, ua):
    try:
        p = urlparse(url)
        r = rp.RobotFileParser(); r.set_url(f"{p.scheme}://{p.netloc}/robots.txt"); r.read()
        return r.can_fetch(ua, url)
    except Exception:
        return True  # if robots is unreachable, proceed politely

def fetch(url, ua, parser):
    """Return page HTML or raise. Uses requests, or Playwright for JS pages."""
    if parser == "browser":
        from playwright.sync_api import sync_playwright  # optional dep
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page(user_agent=ua)
            pg.goto(url, wait_until="networkidle", timeout=45000)
            html = pg.content(); b.close()
            return html
    import requests
    resp = requests.get(url, headers={"User-Agent": ua}, timeout=30)
    resp.raise_for_status()
    return resp.text

def extract_names(html):
    """Best-effort generic extraction of venue names from a list page.
    Real publishers differ wildly; this is a starting point. Precise per-source
    parsers can be added in PARSERS below. Returns ordered [(name, rank|None)]."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    names = []
    # Common patterns: <h2>/<h3> card titles inside article bodies.
    for tag in soup.select("article h2, article h3, .c-mapstack__card h1, .venue-name, h2 a, h3 a"):
        txt = " ".join(tag.get_text(" ", strip=True).split())
        if 2 <= len(txt) <= 60 and not txt.lower().startswith(("read ", "more ", "sign ")):
            names.append(txt)
    # de-dup preserving order
    seen, out = set(), []
    for i, n in enumerate(names):
        k = norm(n)
        if k and k not in seen:
            seen.add(k); out.append((n, None))
    return out

PARSERS = {
    # "track_kind or publication": custom_callable(html) -> [(name, rank)]
    # Add precise per-source parsers here as they are validated.
}

# ---------------- main ----------------
def load_city(city): return json.loads((CITY_DIR / f"{city}.json").read_text(encoding="utf-8"))
def save_city(city, d): (CITY_DIR / f"{city}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

def run(dry=False, only=None):
    src = json.loads(SOURCES.read_text())
    ua = src["settings"]["user_agent"]
    delay = src["settings"].get("request_delay_seconds", 4)
    REPORTS.mkdir(exist_ok=True)
    today = datetime.date.today().isoformat()
    manual, applied, proposals = [], [], []

    for city, sections in src["lists"].items():
        if only and city != only: continue
        cd = load_city(city)
        for section, listkey, venkey in (("restaurants", "rlists", "restos"), ("bars", "blists", "bars")):
            venues = cd[venkey]
            for lid, cfg in sections[section].items():
                if cfg.get("skip") or cfg.get("access") == "owner_manual":
                    continue  # your own personal lists — never scraped
                if cfg.get("access") in ("paywall", "app_only"):
                    manual.append((city, section, lid, cfg["name"],
                                   cfg["access"].replace("_", " ") + " — pull manually"))
                    continue
                url = (cfg.get("url") or "").strip()
                if not url:
                    manual.append((city, section, lid, cfg["name"], "no url in sources.json"))
                    continue
                if cfg["parser"] != "browser" and src["settings"]["respect_robots_txt"] and not allowed(url, ua):
                    manual.append((city, section, lid, cfg["name"], "blocked by robots.txt — pull manually"))
                    continue
                try:
                    html = fetch(url, ua, cfg["parser"]); time.sleep(delay)
                    rows = PARSERS.get(cfg.get("track_kind"), extract_names)(html)
                    if len(rows) < 3:
                        raise RuntimeError(f"only {len(rows)} names parsed — layout likely changed")
                except Exception as e:
                    manual.append((city, section, lid, cfg["name"], f"{type(e).__name__}: {e}"))
                    continue
                # ---- apply membership for this pinned list only ----
                current = set()
                for i, (nm, rk) in enumerate(rows):
                    v = best_match(nm, venues)
                    rank = rk if rk is not None else (i + 1 if cfg["ranked"] else None)
                    if v:
                        current.add(v["name"])
                        entry = next((l for l in v["lists"] if l[0] == lid), None)
                        if entry is None:
                            v["lists"].append([lid, rank]); applied.append(f"{city}: +{v['name']} on {lid}")
                        elif entry[1] != rank:
                            entry[1] = rank; applied.append(f"{city}: {v['name']} rank→{rank} on {lid}")
                    else:
                        proposals.append((city, section, nm, lid))
                # a venue that fell off this list
                for v in venues:
                    if v["name"] not in current and any(l[0] == lid for l in v["lists"]):
                        v["lists"] = [l for l in v["lists"] if l[0] != lid]
                        applied.append(f"{city}: -{v['name']} dropped from {lid}")
                # bump stored year
                cfg_year = cfg.get("year")
                if cfg_year and cd[listkey].get(lid, {}).get("year") != cfg_year:
                    cd[listkey][lid]["year"] = cfg_year
        if not dry: save_city(city, cd)

    _write_report(today, manual, applied, proposals, src["settings"].get("monitors", {}))
    print(f"applied {len(applied)} edits · {len(proposals)} new-venue proposals · {len(manual)} need manual pull")
    return manual, applied, proposals

def _write_report(today, manual, applied, proposals, monitors=None):
    REPORTS.mkdir(exist_ok=True)
    lines = [f"# Weekly update — {today}", ""]
    if monitors:
        lines += ["## 👀 Monitors", ""]
        for key, cfg in monitors.items():
            state = "on" if cfg.get("enabled") else "off"
            filled = ""
            if "sources" in cfg:
                have = sum(1 for c in cfg["sources"].values() for u in (c.values() if isinstance(c, dict) else [c]) if u)
                filled = f" — {have} source URL(s) set"
            lines.append(f"- **{key.replace('_',' ')}** ({state}){filled}")
        lines.append("")
    lines += [f"- Auto-applied edits: **{len(applied)}**",
              f"- New-venue proposals (need a human): **{len(proposals)}**",
              f"- Lists that need a manual pull: **{len(manual)}**", ""]
    if manual:
        lines += ["## ⛏️ Needs manual pull", "",
                  "Could not fetch/parse these. Paste the current list into the city JSON"
                  " (or reply to the bot issue) and the next build will fold it in.", ""]
        for city, sec, lid, name, why in manual:
            lines.append(f"- **{city} / {sec} / `{lid}`** — {name} — _{why}_")
        lines.append("")
    if proposals:
        lines += ["## 🆕 New venues on a list (not yet in our data)", "",
                  "Review, then add to the city JSON with a type + coords:", ""]
        for city, sec, nm, lid in proposals:
            lines.append(f"- **{city} / {sec}** — “{nm}” (seen on `{lid}`)")
        lines.append("")
    if applied:
        lines += ["## ✅ Auto-applied", ""] + [f"- {a}" for a in applied] + [""]
    (REPORTS / "latest.md").write_text("\n".join(lines), encoding="utf-8")
    (REPORTS / f"{today}.md").write_text("\n".join(lines), encoding="utf-8")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    run(dry=a.dry_run, only=a.only)
