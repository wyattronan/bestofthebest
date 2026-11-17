#!/usr/bin/env python3
"""Add a dedicated lunch list to a city: new venues + tags on existing ones.
Reusable across cities. Re-running is idempotent for a given listid."""
import json, sys, os

CASUAL_VB={'quick','lunch','bbq','taco','pizza','cheesesteak','latindc','taqueria','deli','healthy'}
PORT_TYPE={'deli','bakery','quick','pizza','bbq','cheesesteak'}
def is_to(v):
    if v.get('cl'): return False
    vb=v.get('vb'); t=v.get('type'); pr=v.get('pr') or 3
    if vb in ('tasting','datenight') or t=='tasting': return False
    if vb in CASUAL_VB: return True
    if vb=='asian' and pr<=2: return True
    if vb=='specialty' and pr<=2: return True
    if t in PORT_TYPE: return True
    return False

def classify(types, pr):
    T=set(types or []); pr=pr or 2
    def has(*xs): return any(x in T for x in xs)
    if has('taco_restaurant') or (has('mexican_restaurant') and pr<=2): return 'mexican','taco'
    if has('mexican_restaurant'): return 'mexican','datenight'
    if has('pizza_restaurant'): return 'pizza','pizza'
    if has('italian_restaurant'): return ('italian','italian') if pr>=3 else ('italian','italian')
    if has('indian_restaurant'): return 'indian','global'
    if has('french_restaurant'): return 'french','datenight'
    if has('japanese_restaurant','sushi_restaurant','ramen_restaurant'): return ('japanese','tasting') if pr>=4 else ('japanese','asian')
    if has('chinese_restaurant','cantonese_restaurant','dim_sum_restaurant','thai_restaurant','vietnamese_restaurant','korean_restaurant','indonesian_restaurant','asian_restaurant','noodle_shop'): return 'asian','asian'
    if has('mediterranean_restaurant','middle_eastern_restaurant','greek_restaurant','lebanese_restaurant','turkish_restaurant'): return 'med','global'
    if has('barbecue_restaurant'): return 'bbq','bbq'
    if has('seafood_restaurant'): return 'seafood','datenight'
    if has('steak_house'): return 'steak','datenight'
    if has('sandwich_shop','deli'): return 'deli','quick'
    if has('bakery','cafe','breakfast_restaurant','brunch_restaurant','coffee_shop','donut_shop'): return 'bakery','brunch'
    if has('ethiopian_restaurant','african_restaurant','latin_american_restaurant','caribbean_restaurant','peruvian_restaurant','spanish_restaurant','brazilian_restaurant'): return 'global','global'
    if has('hamburger_restaurant','fast_food_restaurant','fried_chicken_takeaway'): return 'quick','quick'
    if has('gastropub'): return 'gastropub','datenight' if pr>=3 else 'global'
    if has('american_restaurant','bar','pub'): return 'newam','datenight' if pr>=3 else 'global'
    return 'newam','global'

def hood_from_addr(addr, city):
    # crude: take the street + city is not a neighborhood; leave blank, caller may override
    return ''

def run_auto(city, listid, meta, existing_names, new_places, overrides=None):
    """new_places: list of raw places_search entries (dicts w/ name,latitude,longitude,types,price_level).
    overrides: dict name-> {hood?,type?,vb?,pr?} to correct the auto-classifier."""
    overrides=overrides or {}
    nv=[]
    for pl in new_places:
        o=overrides.get(pl['name'],{})
        st,vb=classify(pl.get('types'), pl.get('price_level'))
        nv.append({'name':o.get('rename',pl['name']),'hood':o.get('hood',''),
                   'type':o.get('type',st),'vb':o.get('vb',vb),
                   'lat':pl['latitude'],'lng':pl['longitude'],
                   'pr':o.get('pr', pl.get('price_level') or 2)})
    return run(city, listid, meta, existing_names, nv)

def run(city, listid, meta, existing_names, new_venues):
    p=f'data/cities/{city}.json'
    d=json.load(open(p))
    # add list meta
    d['rlists'][listid]=meta
    byname={v['name']:v for v in d['restos']}
    # tag existing
    tagged=0; miss=[]
    for nm in existing_names:
        v=byname.get(nm)
        if not v: miss.append(nm); continue
        if not any(l[0]==listid for l in v['lists']):
            v['lists'].append([listid,None]); tagged+=1
    # add new
    added=0
    for nv in new_venues:
        if nv['name'] in byname:
            v=byname[nv['name']]
            if not any(l[0]==listid for l in v['lists']):
                v['lists'].append([listid,None])
            continue
        rec={'name':nv['name'],'hood':nv['hood'],'type':nv['type'],'typekind':'cui',
             'lat':nv['lat'],'lng':nv['lng'],'pr':nv['pr'],
             'lists':[[listid,None]],'dual':False,'vb':nv['vb']}
        if is_to(rec): rec['to']=1
        d['restos'].append(rec); added+=1
    json.dump(d,open(p,'w'),ensure_ascii=False,indent=1)
    print(f"{city}: list '{listid}' added | tagged {tagged} existing, added {added} new"
          + (f" | MISSING existing: {miss}" if miss else ""))
