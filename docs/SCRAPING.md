# How the weekly update works

The site's data lives in **`data/cities/*.json`** (one file per city). `index.html`
is the single deployed artifact; its data blob is *built* from those files by
`scripts/build.py`. You never hand-edit the data inside `index.html`.

```
data/cities/<city>.json   ← source of truth (restos, bars, rlists, blists)
data/sources.json         ← which list to re-scrape, and from what URL
scripts/update.py         ← fetch + fold changes into data/
scripts/build.py          ← data/ → CITIES_DATA inside index.html
.github/workflows/weekly-update.yml  ← runs it all, weekly, automatically
```

## The weekly job (no approval needed)
Every Sunday (and on demand from the Actions tab) GitHub Actions:
1. runs `update.py` — re-fetches each tracked list, refreshes membership/rank,
   marks closures, proposes brand-new venues;
2. runs `build.py` — folds the data back into `index.html`;
3. commits & pushes — which triggers your Netlify deploy;
4. opens a GitHub **issue** listing anything it couldn't fetch.

## "Pinned" lists — same list, year over year
Each entry in `data/sources.json` names *one specific, prestigious list* (e.g.
*Eater's 38 Essential Restaurants*). The scraper only ever updates **that** list.
A publication's other, lesser roundups ("best new", "where to eat this month")
are ignored, so prestige stays consistent across years. To start tracking a
different list, change its `url`/identity in `sources.json`.

## What auto-applies vs. what waits for you
| Change | Behavior |
|---|---|
| A venue's rank changes on a tracked list | auto-applied |
| A venue drops off / joins a tracked list | auto-applied |
| A venue closes | auto-marked closed (kept, struck-through) |
| A brand-new venue appears on a list | **proposed** in the issue (needs a type + coords) |
| A list page can't be fetched/parsed | **listed in the issue** for a manual pull |

Tune this in `sources.json → settings.auto_apply`.

## The manual-pull fallback
Many publishers (Michelin, The Infatuation, paywalled or Cloudflare-protected
pages) block automated fetching — and GitHub's runners are often blocked too.
When that happens the list shows up in the weekly issue. To refresh it by hand,
paste the current names into the city JSON's venues (add/remove the list's id in
each venue's `lists`), or just tell me the list and I'll fold it in.

## How each source is reached (`access` tag)
Every list in `sources.json` is tagged by how it can be fetched:

| `access` | meaning | automatable? |
|---|---|---|
| `web_scrape` | plain HTML list page (Eater, Time Out, PUNCH, Resy, city mags, Beard) | yes (needs the URL) |
| `js_render` | JavaScript page (Michelin, The Infatuation) — uses a headless browser | sometimes; often blocked |
| `paywall` | NYT, Condé Nast, Bon Appétit, SF Chronicle, LA Times, Boston Globe | no → manual pull |
| `app_only` | Beli (rankings live in the app) | no → manual pull |
| `owner_manual` | your own "Wyatt's Top…" lists | never scraped |

Current split: ~48 web-scrapable, ~25 JS, ~47 paywalled, ~11 app-only, 4 yours.
Realistically the paywalled/app/JS sources flow through the weekly manual-pull
issue — the automatable share is the ~48 web pages once their URLs are filled.

## Monitors (beyond list refreshes)
`sources.json → settings.monitors` adds three watchers:
- **awards** — Michelin stars / James Beard winners / World's 50 Best changes
  update those lists' memberships. (Fill per-city award page URLs.)
- **closures_relocations** — closures mark `cl:true` (kept, struck-through);
  relocations update neighborhood + coordinates. (Fill per-city Eater feeds.)
- **new_lists** — when a watched publication posts a *new* prestigious city
  list, it's flagged for your approval before being added (never auto-added).

## Filling in the URLs
`data/sources.json` is pre-populated with every tracked list's identity but the
`url` fields are blank. Add the canonical page URL for each pinned list to turn
automation on for it. No URL = that list stays on the manual-pull path.
