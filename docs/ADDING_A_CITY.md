# Adding a new city tab

The data refactor makes this a data task, not a code task.

1. **Create `data/cities/<city>.json`** with the four keys (copy
   `data/cities/_TEMPLATE.json` or an existing city as a starting point):
   - `restos` — array of restaurants
   - `bars` — array of bars
   - `rlists` — restaurant list definitions (the credit chips)
   - `blists` — bar list definitions

   Each venue looks like:
   ```json
   {"name":"Place","hood":"Neighborhood","type":"italian","typekind":"cui",
    "lat":41.88,"lng":-87.65,"pr":2,"vg":1,
    "lists":[["eater38",null],["cnt33",3]],"vb":"datenight"}
   ```
   - `type` restaurants: italian, french, med, japanese, asian, mexican, latin,
     seafood, steak, newam, tasting, pizza, bbq, southern, gastropub, bakery,
     classics, global, indian. Bars: `m` (cocktails), `b` (beer/tavern), `w` (wine).
   - `pr` 1–4 (price), `vg`/`vn` veg/vegan flags, `tg` tasting flag, `cl` closed.
   - `lists` = `[listId, rankOrNull]` pairs. `vb` = tier id (see the tier logic
     in index.html: specialty, pizza, italian, datenight, tasting, oldguard,
     quick, brunch, global, deli, asian, healthy, taco, taqueria, latindc; bars:
     mixo, livemusic, dive, wine, vibey, party, brewery, tiki).

2. **Register it** in `data/cities/_order.json` (controls tab order) and add the
   city's masthead sign/skyline + center coords in `index.html` (the per-city
   CSS/markup blocks and the `CTR` map-center object).

3. **Add its lists** to `data/sources.json` under `lists.<city>` so the weekly
   job tracks them.

4. **Build & preview:** `python3 scripts/build.py`, open `index.html`.

(If you give me a city's lists, I can generate the whole JSON — geocoding,
types and tier tags included — and wire up the masthead.)
