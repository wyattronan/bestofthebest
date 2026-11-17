"""Homepage map -> stamp album, with true geolocated city dots.
Run from the repo root:  python3 scripts/apply_homepage_stamps.py index.html
Stdlib only. Reuses the medallion images already in index.html."""
import re,json,math,sys
P=sys.argv[1] if len(sys.argv)>1 else 'index.html'
h=open(P,encoding='utf-8').read()
# Dot positions: real lat/lng projected with the map's own Albers equal-area conic (fit to 21 state corners, ~0.5 unit RMS)
NEW={"seattle":[370.3,43.7],"portland":[351.9,86.6],"sanfrancisco":[306.2,253.6],"losangeles":[357.1,353.8],"sandiego":[369.7,387.5],"lasvegas":[423.1,320.5],"phoenix":[466.7,391.0],"denver":[611.9,269.2],"austin":[732.1,487.8],"dallas":[751.0,432.3],"houston":[778.5,499.3],"kansascity":[790.6,290.9],"twincities":[809.3,159.0],"neworleans":[882.1,491.2],"chicago":[905.0,222.4],"milwaukee":[898.1,196.9],"nashville":[932.1,348.3],"atlanta":[981.9,396.7],"triangle":[1074.6,333.3],"miami":[1090.0,558.8],"washington":[1093.0,260.9],"philadelphia":[1119.4,231.0],"newyork":[1134.6,209.8],"boston":[1172.8,161.5]}
LATLON={'seattle':(47.6062,-122.3321),'portland':(45.5152,-122.6784),'sanfrancisco':(37.7749,-122.4194),'losangeles':(34.0522,-118.2437),'sandiego':(32.7157,-117.1611),'lasvegas':(36.1699,-115.1398),'phoenix':(33.4484,-112.0740),'denver':(39.7392,-104.9903),'austin':(30.2672,-97.7431),'dallas':(32.7767,-96.7970),'houston':(29.7604,-95.3698),'kansascity':(39.0997,-94.5786),'twincities':(44.9778,-93.2650),'neworleans':(29.9511,-90.0715),'chicago':(41.8781,-87.6298),'milwaukee':(43.0389,-87.9065),'nashville':(36.1627,-86.7816),'atlanta':(33.7490,-84.3880),'triangle':(35.8992,-78.8636),'miami':(25.7617,-80.1918),'washington':(38.9072,-77.0369),'philadelphia':(39.9526,-75.1652),'newyork':(40.7128,-74.0060),'boston':(42.3601,-71.0589)}
i0=h.index('<div class="hp-map">');s0=h.index('<svg',i0);s1=h.index('</svg>',s0)+6
svg=h[s0:s1]
states=re.search(r'<g class="hp-states">.*?</g>',svg,re.S).group(0)
pins=[]
for m in re.finditer(r'<g class="hp-pin" data-go="([^"]+)"[^>]*aria-label="([^"]+)">(.*?)</g>',svg,re.S):
  go,label,inner=m.groups();k=go.split('/')[1]
  img=re.search(r'<image href="([^"]+)"',inner).group(1)
  name=re.search(r'<text class="hp-card-name"[^>]*>([^<]+)</text>',inner).group(1)
  pins.append(dict(k=k,go=go,label=label,img=img,name=name))
assert len(pins)==24,len(pins)
assert set(p['k'] for p in pins)==set(NEW),set(p['k'] for p in pins)^set(NEW)
# Stamp slot per city (min-total-distance assignment around the frame; 0 crossing leader lines)
SLOT={"atlanta":[1271,690],"austin":[636,690],"boston":[1271,-100],"chicago":[1017,-100],"dallas":[509,690],"denver":[509,-100],"houston":[763,690],"kansascity":[636,-100],"lasvegas":[170,250],"losangeles":[170,405],"miami":[1144,690],"milwaukee":[890,-100],"nashville":[1017,690],"neworleans":[890,690],"newyork":[1350,95],"philadelphia":[1144,-100],"phoenix":[382,690],"portland":[255,-100],"sandiego":[255,690],"sanfrancisco":[170,95],"seattle":[382,-100],"triangle":[1350,405],"twincities":[763,-100],"washington":[1350,250]}
SHORT={'washington':'Washington','twincities':'Minneapolis'}
ABBR={'seattle':'SEA','portland':'PDX','sanfrancisco':'SF','losangeles':'LA','sandiego':'SD','lasvegas':'LV','phoenix':'PHX','denver':'DEN','austin':'ATX','dallas':'DAL','houston':'HOU','kansascity':'KC','twincities':'MSP','neworleans':'NOLA','chicago':'CHI','milwaukee':'MKE','nashville':'NASH','atlanta':'ATL','triangle':'TRI','miami':'MIA','washington':'DC','philadelphia':'PHL','newyork':'NYC','boston':'BOS'}
out=['<svg viewBox="95 -170 1330 930" role="group" aria-label="Choose a city: stamps around the map link to each city guide">',
 '<defs><clipPath id="hp-sp-clip"><rect x="-40" y="-48" width="80" height="68"/></clipPath></defs>',states]
order=sorted(range(24),key=lambda i:pins[i]['k'])
if '<g class="hp-pin" data-go' in svg and 'hp-sp-' in svg: sys.exit('Stamps already applied')
for n,i in enumerate(order):
  p=pins[i];k=p['k'];x,y=NEW[k];sx,sy=SLOT[k];la,lo=LATLON[k]
  rot=((n*37)%7-3)*.9
  g=[f'<g class="hp-pin" data-go="{p["go"]}" data-city="{k}" tabindex="0" role="button" aria-label="{p["label"]}">',
     f'<line class="hp-sp-lead" x1="{sx}" y1="{sy}" x2="{x}" y2="{y}"/>',
     f'<g class="hp-sp-post"><circle cx="{x}" cy="{y}" r="15"/><circle cx="{x}" cy="{y}" r="11"/>'+''.join(f'<path d="M{x+18:.1f} {y-6+j*6:.1f} q6 -4 12 0 t12 0 t12 0"/>' for j in range(3))+'</g>',
     f'<circle class="hp-sp-dot" cx="{x}" cy="{y}" r="3.6"><title>{p["name"]} ({la:.4f}, {lo:.4f})</title></circle>',
     f'<g transform="translate({sx},{sy}) rotate({rot:.1f})"><g class="hp-sp-card">',
     '<rect class="hp-sp-shadow" x="-46" y="-54" width="96" height="112"/><rect class="hp-sp-bg" x="-48" y="-56" width="96" height="112"/>']
  holes=''.join(f'<circle class="hp-sp-hole" cx="{q}" cy="-56" r="2.6"/><circle class="hp-sp-hole" cx="{q}" cy="56" r="2.6"/>' for q in range(-48,49,8))
  holes+=''.join(f'<circle class="hp-sp-hole" cx="-48" cy="{q}" r="2.6"/><circle class="hp-sp-hole" cx="48" cy="{q}" r="2.6"/>' for q in range(-48,49,8))
  g.append(holes)
  g.append(f'<image href="{p["img"]}" x="-40" y="-48" width="80" height="68" preserveAspectRatio="xMidYMid slice" clip-path="url(#hp-sp-clip)"/>')
  g.append('<rect class="hp-sp-inner" x="-40" y="-48" width="80" height="68"/>')
  g.append(f'<text class="hp-sp-den" x="-35" y="-31" data-den="{k}"></text><text class="hp-sp-denu" x="-35" y="-23">LISTS</text>')
  g.append(f'<text class="hp-sp-name" x="0" y="38">{SHORT.get(k,p["name"])}</text>')
  g.append(f'<text class="hp-sp-denu hp-sp-postage" x="0" y="49">U.S. POSTAGE · {ABBR[k]}</text>')
  g.append('</g></g></g>')
  out.append(''.join(g))
out.append('</svg>')
h=h[:s0]+''.join(out)+h[s1:]
# CSS: replace old map rules
c0=h.index('.hp-state{fill:#d6ccb4');c1=h.index('\n',h.index('@media(max-width:620px){.hp-card-name'))+1
CSS='''.hp-state{fill:#d6ccb4;stroke:#efe9da;stroke-width:1.3;}
.hp-pin{cursor:pointer;}
.hp-pin:focus{outline:none;}
.hp-sp-lead{stroke:#8a0f12;stroke-width:1;stroke-dasharray:2 4;opacity:.35;transition:opacity .2s,stroke-width .2s;}
.hp-sp-dot{fill:#8a0f12;}
.hp-sp-post{opacity:0;transition:opacity .2s;fill:none;stroke:#2a3a7a;stroke-width:1.4;pointer-events:none;}
.hp-sp-card{transform-box:fill-box;transform-origin:center;transition:transform .25s cubic-bezier(.2,.8,.2,1);}
.hp-pin:hover .hp-sp-card,.hp-pin:focus-visible .hp-sp-card{transform:translateY(-6px) scale(1.06);}
.hp-pin:hover .hp-sp-lead,.hp-pin:focus-visible .hp-sp-lead{opacity:1;stroke-width:1.8;stroke-dasharray:none;}
.hp-pin:hover .hp-sp-post,.hp-pin:focus-visible .hp-sp-post{opacity:.85;}
.hp-sp-shadow{fill:rgba(0,0,0,.18);filter:blur(2px);}
.hp-sp-bg{fill:#f7f2e6;}
.hp-sp-hole{fill:#e2dbc8;}
.hp-sp-inner{fill:none;stroke:#1a1712;stroke-width:.6;opacity:.5;}
.hp-sp-name{font-family:'AccentSerif','Fraunces',Georgia,serif;font-weight:700;font-size:11px;text-anchor:middle;fill:#1a1712;}
.hp-sp-den{font-family:'AccentSerif','Fraunces',Georgia,serif;font-weight:900;font-size:17px;fill:#fff;paint-order:stroke;stroke:rgba(0,0,0,.55);stroke-width:2.5;}
.hp-sp-denu{font-family:'AccentSans','Space Grotesk',sans-serif;font-size:6px;letter-spacing:.12em;fill:#fff;}
.hp-sp-postage{fill:#8a0f12;text-anchor:middle;}
@media(max-width:620px){.hp-sp-name{font-size:13px;}}
'''
h=h[:c0]+CSS+h[c1:]
# JS: stamp denominations from live data, keyboard + raise-on-hover
anchor='document.querySelectorAll("#homepage [data-go]").forEach(el=>el.onclick=function(e){e.stopPropagation();location.hash=el.dataset.go;});\n'
assert h.count(anchor)==1
JS=anchor+'''(function(){document.querySelectorAll("#homepage [data-den]").forEach(function(t){var d=CITIES_DATA[t.getAttribute("data-den")];t.textContent=d&&d.rlists?Object.keys(d.rlists).length:"";});
  document.querySelectorAll("#homepage .hp-pin").forEach(function(g){function raise(){if(g.parentNode.lastElementChild!==g)g.parentNode.appendChild(g);}g.addEventListener("mouseenter",raise);g.addEventListener("focus",function(){if(g.parentNode.lastElementChild!==g){raise();g.focus();}});g.addEventListener("keydown",function(e){if(e.key==="Enter"||e.key===" "){e.preventDefault();location.hash=g.dataset.go;}});});})();
'''
h=h.replace(anchor,JS)
open(P,'w',encoding='utf-8').write(h)
print('ok',len(h))
