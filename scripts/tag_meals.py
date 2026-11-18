"""Tag every restaurant with the meals it serves: ml = subset of 'brld'
(b=breakfast, r=brunch, l=lunch, d=dinner). Heuristic from section, cuisine,
price, name, notes and lunch-list membership. Existing manual 'mlx' overrides win."""
import json, pathlib, re, collections
D = pathlib.Path('data/cities')
TX = {'austin','dallas','houston'}
BAKE_T = {'bakery','brunch','cafe'}
MORNING = re.compile(r"\b(bagels?|donuts?|doughnuts?|biscuits?|pancakes?|waffles?|breakfast|bakery|bakeshop|panader[ií]a|patisserie|pâtisserie|boulangerie|bread|pastry|pastries|kolaches?|coffee|croissant)\b", re.I)
DAYONLY = re.compile(r"\b(bagels?|donuts?|doughnuts?|biscuits?|pancakes?|breakfast|bakery|bakeshop|panader[ií]a|patisserie|pâtisserie|boulangerie|pastry|kolaches?|coffee|croissant)\b", re.I)
CAFE = re.compile(r"\bcaf[eé]\b", re.I)
DINER = re.compile(r"\bdiner\b", re.I)
WORD_T = {'bakery','brunch','cafe','newam','american','classics','quick','southern','soul','deli','sandwich','bbq','french'}
OVR = {('neworleans',"Commander's Palace"):'rld', ('neworleans',"Brennan's"):'brld', ('neworleans','Elizabeth\'s'):'brld', ('austin','Franklin Barbecue'):'l', ('austin','la Barbecue'):'l', ('austin',"Snow's BBQ"):'bl'}
LUNCH_VB = {'quick','taco','taqueria','bbq','pizza','cheesesteak','deli','healthy','brunch'}
LUNCH_T = {'deli','sandwich','quick','bbq','pizza','cheesesteak','hoagie','bakery','brunch','cafe','hotdog','soul'}

def meals(c, v):
    if v.get('mlx'): return v['mlx']
    if (c, v['name']) in OVR: return OVR[(c, v['name'])]
    n = v['name']; t = v['type']; vb = v.get('vb'); pr = v.get('pr') or 2
    note = (v.get('note') or '').lower()
    tasting = t == 'tasting' or vb == 'tasting' or v.get('tg') or bool(re.search(r'omakase', n, re.I)) or v.get('sub') in ('Kaiseki','Kappo')
    wordy = t in WORD_T
    cafe_like = t in BAKE_T or vb == 'brunch' or (wordy and bool(DAYONLY.search(n))) \
        or (CAFE.search(n) and pr <= 2 and t in {'american','classics','quick','bakery','brunch'})
    b = r = l = d = False
    # breakfast
    if t in BAKE_T or vb == 'brunch' or (wordy and MORNING.search(n)) or 'breakfast' in note: b = True
    if CAFE.search(n) and pr <= 2 and t in {'newam','american','classics','quick','bakery','brunch','southern','soul'}: b = True
    if DINER.search(n) and pr <= 2: b = True
    if t == 'deli' or vb == 'deli' or re.search(r'\bdeli(catessen)?\b', n, re.I): b = True
    if c in TX and (vb in {'taco','taqueria'} or (t == 'mexican' and pr == 1)): b = True
    # brunch
    if vb == 'brunch' or t == 'brunch' or 'brunch' in n.lower() or 'brunch' in note: r = True
    if DINER.search(n) and pr <= 2: r = True
    # lunch
    if v.get('lu') or 'lunch' in note: l = True
    if vb in LUNCH_VB or t in LUNCH_T: l = True
    if vb == 'latindc' and pr <= 2: l = True
    if vb == 'oldguard' and t not in {'steak','steakhouse'}: l = True
    if pr <= 2 and not tasting and vb not in ('datenight','italian'): l = True
    if tasting and not v.get('lu'): l = False
    # dinner
    d = True
    if cafe_like:
        d = t not in BAKE_T and not (wordy and DAYONLY.search(n)) and pr >= 2
    if t == 'sandwich' or (t == 'deli' and pr < 2): d = False
    if not (b or r or l or d): d = True
    return ''.join(k for k, on in zip('brld', (b, r, l, d)) if on)

cnt = collections.Counter(); combos = collections.Counter(); samples = collections.defaultdict(list)
for f in sorted(D.glob('[a-z]*.json')):
    data = json.loads(f.read_text(encoding='utf-8'))
    for v in data['restos']:
        m = meals(f.stem, v); v['ml'] = m; combos[m] += 1
        for k in m: cnt[k] += 1
        samples[m].append(f"{f.stem[:4]}:{v['name']}")
    f.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
print(cnt); print(combos.most_common())
import random; random.seed(3)
for m in combos: print(m, random.sample(samples[m], min(12, len(samples[m]))))
