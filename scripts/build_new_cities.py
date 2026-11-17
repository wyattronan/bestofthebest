#!/usr/bin/env python3
"""Build charleston/baltimore/detroit JSON from geocoded TSVs + list membership."""
import json, re, os
GEO="/tmp/claude-0/-home-claude/3bad3a39-e70c-5398-88c1-48d74ebf8e65/scratchpad/geo"
OUT="/home/claude/bestofthebest/data/cities"

def norm(s):
    s=s.lower().strip()
    s=re.sub(r"^the ","",s)
    s=re.sub(r"[^a-z0-9]","",s)
    for suf in ("restaurant","charleston","baltimore","detroit","oysterbar","kitchen"):
        pass
    return s

def match(name, members):
    n=norm(name)
    for m in members:
        mm=norm(m)
        if not n or not mm: continue
        if n==mm: return True
        if len(n)>=5 and len(mm)>=5 and (n in mm or mm in n): return True
    return False

# Charleston cuisine -> vb tier
CHS_VB={
 "seafood":"specialty","italian":"italian","pizza":"italian","french":"datenight",
 "american":"datenight","southern":"oldguard","soul":"oldguard","bbq":"bbq",
 "chinese":"asian","japanese":"asian","vietnamese":"asian","filipino":"asian","asian":"asian","ramen":"asian",
 "mexican":"global","spanish":"global","greek":"global","indian":"global","pakistani":"global",
 "african":"global","steakhouse":"datenight","sandwich":"quick","british":"quick","global":"global"}

def read_tsv(path, is_bar):
    rows=[]
    for line in open(path, encoding="utf-8"):
        line=line.rstrip("\n")
        if not line.strip(): continue
        p=line.split("\t")
        name=p[0]; lat=float(p[1]); lng=float(p[2])
        pr=int(p[3]) if len(p)>3 and p[3].strip() else 2
        typ=p[4] if len(p)>4 else ""
        hood=p[5] if len(p)>5 else ""
        vb=p[6] if len(p)>6 else ""
        rows.append(dict(name=name,lat=lat,lng=lng,pr=pr,typ=typ,hood=hood,vb=vb))
    return rows

def build(resto_rows, bar_rows, rlist_members, blist_members, rlists_meta, blists_meta, chs=False):
    restos=[]
    for r in resto_rows:
        lists=[[lid,None] for lid,mem in rlist_members.items() if match(r["name"],mem)]
        if not lists: lists=[]
        vb=r["vb"] if r["vb"] else CHS_VB.get(r["typ"],"global")
        restos.append({"name":r["name"],"hood":r["hood"],"type":r["typ"],"typekind":"cui",
                       "lat":r["lat"],"lng":r["lng"],"pr":r["pr"],
                       "lists":lists,"dual":False,"vb":vb})
    restos=[x for x in restos if x["lists"]]
    bars=[]
    for r in bar_rows:
        lists=[[lid,None] for lid,mem in blist_members.items() if match(r["name"],mem)]
        if not lists: continue
        bars.append({"name":r["name"],"hood":r["hood"],"type":r["typ"],"typekind":"drink",
                     "lat":r["lat"],"lng":r["lng"],
                     "lists":lists,"dual":False,"vb":r["vb"]})
    # prune lists with zero members to keep meta honest
    used_r={lid for x in restos for lid,_ in x["lists"]}
    used_b={lid for x in bars for lid,_ in x["lists"]}
    rlists_meta={k:v for k,v in rlists_meta.items() if k in used_r}
    blists_meta={k:v for k,v in blists_meta.items() if k in used_b}
    return {"restos":restos,"bars":bars,"rlists":rlists_meta,"blists":blists_meta}

# ---------------- CHARLESTON ----------------
chs_dish=["167 Raw","Basic Kitchen","Berkeley's","Bintu Atelier","Bistronomy by Nico","Cane Pazzo","Chef Loong","Chez Nous","Chubby Fish","Coda del Pesce","Costa","Edison","Estadio","Gabrielle","The Grocery","Hannibal's Kitchen","Husk","Jack of Cups","Jackrabbit Filly","Kultura","Kwei Fei","Laura","Lewis Barbecue","Lillian's Petite Market","Lost Isle","Ma'am Saab","Maya del Sol","Marbled & Fin","The Obstinate Daughter","The Ordinary","Palmira Barbecue","Philosophia","Pink Bellies","Post House","R Kitchen","Rancho Lewis","Renzo","Royal Tern","SHIKI","Sorelle","Southbound","Stella's","Sullivan's Fish Camp","Sushi-Wa","The James","Vern's","Wild Common","Wild Olive","XO Brasserie","Zero George"]
chs_pc=["King BBQ","Cane Pazzo","Palmira Barbecue","Bar George","Lost Isle","Sullivan's Fish Camp","Merci","Volpe","OK Donna","Rivayat","Bareo","Bertha's Kitchen","Hannibal's Kitchen","Bintu Atelier","FIG","Slightly North of Broad","Chubby Fish","Seahorse","167 Raw","Vern's","Malagon","Wild Common","Leon's Oyster Shop","Xiao Bao Biscuit"]
chs_resy=["Costa","Kultura","SHIKI","Vern's","FIG","OK Donna","Merci","Volpe","Sullivan's Fish Camp","Bintu Atelier","Chubby Fish","La Cave","The Pass","Sorelle","Bar Weems","The Codfather","Mex 1 Coastal Cantina","Estadio","Leon's Oyster Shop"]
chs_living=["Lewis Barbecue","Philosophia","Ma'am Saab","Lost Isle"]  # broad-category winners present in set
chs_today=["The Obstinate Daughter","Wild Olive","Marbled & Fin"]
chs_rlist_members={"dish":chs_dish,"pc":chs_pc,"resy":chs_resy,"chliving":chs_living,"chstoday":chs_today}
chs_afar=["The Rarebit","Cane Rhum Bar","Thoroughbred Club","The Belmont","The Gin Joint","The Cocktail Club","Revelry Brewing","Lowlife Bar","Josephine Wine Bar","Graft Wine Shop","Harold's Cabin","Edmund's Oast","Taco Boy","The Royal American","Blind Tiger Pub","Recovery Room Tavern"]
chs_living_bars=["Reds Ice House","Bay Street Biergarten","Holy City Brewing","Blind Tiger Pub","Rooted Bottle Market","Edmund's Oast","The Belmont"]
chs_today_bars=["Holy City Brewing","Recovery Room Tavern","Uptown Social","Avondale Wine & Cheese","Somm Wine Bar","Graft Wine Shop","Edmund's Oast"]
chs_resy_bars=["Felix Cocktails","Seahorse","Stems & Skins"]
chs_blist_members={"afar":chs_afar,"chliving":chs_living_bars,"chstoday":chs_today_bars,"resy":chs_resy_bars}
chs_rlists={
 "dish":{"cls":"plate r-chsdish","mono":"D50","tag":"DISH 50","name":"Charleston City Paper's Dish Top 50","year":"2026","ranked":False,"starChip":False},
 "pc":{"cls":"plate r-chspc","mono":"P&C","tag":"POST & COURIER","name":"The Post and Courier's Restaurants to Try","year":"2026","ranked":False,"starChip":False},
 "resy":{"cls":"plate r-chsresy","mono":"RE","tag":"RESY","name":"Resy's Charleston Hit List","year":"2026","ranked":False,"starChip":False},
 "chliving":{"cls":"plate r-chsliving","mono":"HC","tag":"HOLY CITY","name":"Charleston Living's Best of the Holy City","year":"2026","ranked":False,"starChip":False},
 "chstoday":{"cls":"plate r-chstoday","mono":"CHS","tag":"CHSTODAY","name":"CHStoday's Best Readers' Choice","year":"2025","ranked":False,"starChip":False}}
chs_blists={
 "afar":{"cls":"b-chsafar","mono":"AF","tag":"AFAR","name":"Afar's Best Bars in Charleston","year":"2025","ranked":False,"starChip":False},
 "chliving":{"cls":"b-chsliving","mono":"HC","tag":"HOLY CITY","name":"Charleston Living's Best of the Holy City","year":"2026","ranked":False,"starChip":False},
 "chstoday":{"cls":"b-chstoday","mono":"CHS","tag":"CHSTODAY","name":"CHStoday's Best Readers' Choice","year":"2025","ranked":False,"starChip":False},
 "resy":{"cls":"b-chsresy","mono":"RE","tag":"RESY","name":"Resy's Charleston Hit List","year":"2026","ranked":False,"starChip":False}}
chs=build(read_tsv(f"{GEO}/charleston.tsv",False),read_tsv(f"{GEO}/charleston_bars.tsv",True),
          chs_rlist_members,chs_blist_members,chs_rlists,chs_blists,chs=True)

# ---------------- BALTIMORE ----------------
bal_mag=["Alma Cocina Latina","Ammoora","Ananda","Bunny's Buckets","Cece's","Charleston","Cinghiale","Clavel","Cookhouse","Costiera","The Dara","The Duchess","Dylan's Oyster Cellar","Foraged","Gertrude's","Gunther & Co","Hersh's","La Cuchara","Le Comptoir du Vin","Linwoods","Little Donna's","Love Pomelo","Magdalena","Marta","The Milton Inn","NiHao","Oleum","Peerce's","Peter's Inn","Petit Louis","Preserve","The Prime Rib","Red Pepper Sichuan","Rooted Rotisserie","The Ruxton","Sangam","Tagliata","Thames Street Oyster House","True Chesapeake","Woodberry Tavern","The Wren","Wye Oak Tavern"]
bal_infat=["Clavel","Le Comptoir du Vin","Faidley's","Ammoora","Bunny's Buckets","Alma Cocina Latina","Gertrude's","The Duchess","Little Donna's","Ekiben","Marta","Tavern at Woodberry","Puerto 511","Rooted Rotisserie","Foraged","Petit Louis","Dylan's Oyster Cellar","Toki Underground","Blacksauce","NiHao","The Helmand","Chaps Pit Beef","La Barrita"]
bal_rlist_members={"baltmag":bal_mag,"infat":bal_infat}
bal_bars=["29th Street Tavern","The Back Yard","The Coral Wig","The Club Car","The Dive","Dutch Courage","Fadensonnen","Mama Koko's","Meander","Melanie's at Griffith's Tavern","Old Major","The Pink Flamingo","The Royal Blue","Sisu Bar","Southpaw","Vision House","The Wren"]
bal_visit=["Alma Cocina Latina","The Bluebird Cocktail Room","Bloom's","The Bygone","The Coral Wig","Dutch Courage","The Elk Room","NiHao","Pink Flamingo","R. Bar","Rye","Sally O's","Sugarvale","Southpaw","W.C. Harlan"]
bal_blist_members={"baltmagbars":bal_bars,"visitbmore":bal_visit}
bal_rlists={
 "baltmag":{"cls":"plate r-baltmag","mono":"BM","tag":"BALT MAG","name":"Baltimore Magazine's Best Restaurants","year":"2026","ranked":False,"starChip":False},
 "infat":{"cls":"plate r-balinfat","mono":"IN","tag":"INFAT","name":"The Infatuation's Best Restaurants in Baltimore","year":"2025","ranked":False,"starChip":False}}
bal_blists={
 "baltmagbars":{"cls":"b-baltmag","mono":"BM","tag":"BALT MAG","name":"Baltimore Magazine's Best Bars","year":"2026","ranked":False,"starChip":False},
 "visitbmore":{"cls":"b-balvisit","mono":"VB","tag":"VISIT BMORE","name":"Visit Baltimore's Best Cocktail Bars","year":"2026","ranked":False,"starChip":False}}
bal=build(read_tsv(f"{GEO}/baltimore.tsv",False),read_tsv(f"{GEO}/baltimore_bars.tsv",True),
          bal_rlist_members,bal_blist_members,bal_rlists,bal_blists)

# ---------------- DETROIT ----------------
det_infat=["Medusa","Rose's","Loui's Pizza","Bar Chenin","Tacos Wuey","Vecino","Ladder 4","Selden Standard","Little Liberia","The Congregation","Bar Gabi","Al Ameer","Norm's Diner","Duly's Place","Tall Trees Cafe","Marrow","Mabel Gray","Freya","Noori Pocha","Polish Village Cafe","Baobab Fare","La Palapa Del Parian","Scotty Simpson's","Ima Izakaya","Detroit 75"]
det_tt=["Ladder 4","Marrow","Selden Standard","Mabel Gray","The Whitney","Voyager","Barda","Oak & Reel","SheWolf Pastificio","Saffron De Twah","Flowers of Vietnam","Chartreuse"]
det_rlist_members={"infat":det_infat,"tastingtable":det_tt}
det_mt=["Willis Show Bar","Apparatus Room","Bad Luck Bar","Castalia at Sfumato","Kiesling","Lost River","Second Best","The Sugar House","Ghost Bar","The Keep","The Whiskey Parlor","Candy Bar","The Oakland","Otus Supply","The Library at the Detroit Club","Standby"]
det_blist_members={"mtcocktail":det_mt}
det_rlists={
 "infat":{"cls":"plate r-detinfat","mono":"IN","tag":"INFAT","name":"The Infatuation's Best Restaurants in Detroit","year":"2026","ranked":False,"starChip":False},
 "tastingtable":{"cls":"plate r-dettt","mono":"TT","tag":"TASTING TABLE","name":"Tasting Table's Best Restaurants in Metro Detroit","year":"2026","ranked":False,"starChip":False}}
det_blists={
 "mtcocktail":{"cls":"b-detmt","mono":"MT","tag":"METRO TIMES","name":"Metro Times' 20 Best Craft Cocktail Bars","year":"2026","ranked":False,"starChip":False}}
det=build(read_tsv(f"{GEO}/detroit.tsv",False),read_tsv(f"{GEO}/detroit_bars.tsv",True),
          det_rlist_members,det_blist_members,det_rlists,det_blists)

for name,data in (("charleston",chs),("baltimore",bal),("detroit",det)):
    json.dump(data, open(f"{OUT}/{name}.json","w",encoding="utf-8"), ensure_ascii=False)
    nr=len(data["restos"]); nb=len(data["bars"])
    multi=sum(1 for x in data["restos"]+data["bars"] if len(x["lists"])>=2)
    nolist=sum(1 for x in data["restos"]+data["bars"] if not x["lists"])
    print(f"{name}: {nr} restos, {nb} bars | rlists={list(data['rlists'])} blists={list(data['blists'])} | multi-list={multi} no-list={nolist}")
