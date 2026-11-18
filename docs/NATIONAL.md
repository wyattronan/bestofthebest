# National lists and the USA tab

`data/national.json` holds every national list the site tracks (`lists`) and every
entry on them (`entries`). Each entry carries `metro`: the city tab it belongs
to, or `null` when the venue is in a city without a tab.

## Folding into city tabs

Entries with a `metro` are folded into that city's JSON as their own list (the
list def gets a `nat` id, e.g. `"nat": "esq26"`), exactly like any local critic.
Venues already in the tab get the list added; venues that weren't get a new
record (`"_natadd": 1`). Venues whose location couldn't be confirmed have no
`lat`/`lng`, so they show in lists and tables but not on the map.

Lists folded in before this file existed (NYT 2025, North America's 50 Best,
Condé Nast 50/100, USA Today 2025 bars) are tagged with a `nat` id too. Only
their city-tab entries exist, so they're marked `partial` in `national.json`.

## USA tab (`#/usa/restaurants`, `#/usa/bars`)

Built by `scripts/build.py` into `const USA_DATA` in `index.html`:

- **Most National Lists**: every venue on at least one national list, ranked by
  how many distinct national lists name it. City-tab venues are read from their
  tab; entries from cities without a tab come from `national.json`.
- **Top 25 · Share of City Lists**: the 25 venues on the biggest share of their
  own city tab's published lists. Wyatt's personal lists are excluded from both
  sides of the fraction, and a city needs at least `MIN_POOL` (5) published
  lists to qualify (change it at the top of `build.py`).
