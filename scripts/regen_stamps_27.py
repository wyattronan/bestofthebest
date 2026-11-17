#!/usr/bin/env python3
"""Rebuild homepage stamp map for 27 cities (adds Charleston/Baltimore/Detroit)."""
import re, base64, io, sys
from PIL import Image
P="/home/claude/bestofthebest/index.html"
FR="/tmp/claude-0/-home-claude/3bad3a39-e70c-5398-88c1-48d74ebf8e65/scratchpad/frames"

NEW={"seattle":[370.3,43.7],"portland":[351.9,86.6],"sanfrancisco":[306.2,253.6],"losangeles":[357.1,353.8],"sandiego":[369.7,387.5],"lasvegas":[423.1,320.5],"phoenix":[466.7,391.0],"denver":[611.9,269.2],"austin":[732.1,487.8],"dallas":[751.0,432.3],"houston":[778.5,499.3],"kansascity":[790.6,290.9],"twincities":[809.3,159.0],"neworleans":[882.1,491.2],"chicago":[905.0,222.4],"milwaukee":[898.1,196.9],"nashville":[932.1,348.3],"atlanta":[981.9,396.7],"triangle":[1074.6,333.3],"miami":[1090.0,558.8],"washington":[1093.0,260.9],"philadelphia":[1119.4,231.0],"newyork":[1134.6,209.8],"boston":[1172.8,161.5],"charleston":[1067.8,406.7],"baltimore":[1098.3,251.2],"detroit":[978.0,203.7]}
LATLON={'seattle':(47.6062,-122.3321),'portland':(45.5152,-122.6784),'sanfrancisco':(37.7749,-122.4194),'losangeles':(34.0522,-118.2437),'sandiego':(32.7157,-117.1611),'lasvegas':(36.1699,-115.1398),'phoenix':(33.4484,-112.0740),'denver':(39.7392,-104.9903),'austin':(30.2672,-97.7431),'dallas':(32.7767,-96.7970),'houston':(29.7604,-95.3698),'kansascity':(39.0997,-94.5786),'twincities':(44.9778,-93.2650),'neworleans':(29.9511,-90.0715),'chicago':(41.8781,-87.6298),'milwaukee':(43.0389,-87.9065),'nashville':(36.1627,-86.7816),'atlanta':(33.7490,-84.3880),'triangle':(35.8992,-78.8636),'miami':(25.7617,-80.1918),'washington':(38.9072,-77.0369),'philadelphia':(39.9526,-75.1652),'newyork':(40.7128,-74.0060),'boston':(42.3601,-71.0589),'charleston':(32.7765,-79.9311),'baltimore':(39.2904,-76.6122),'detroit':(42.3314,-83.0458)}
SLOT={"seattle":[170,-100],"portland":[170,55],"sanfrancisco":[170,210],"lasvegas":[170,365],"losangeles":[170,520],"newyork":[1350,60],"philadelphia":[1350,166],"baltimore":[1350,272],"washington":[1350,378],"triangle":[1350,484],"charleston":[1350,590],"denver":[509,-100],"kansascity":[636,-100],"twincities":[763,-100],"milwaukee":[890,-100],"chicago":[1017,-100],"detroit":[1144,-100],"boston":[1271,-100],"sandiego":[255,690],"phoenix":[382,690],"dallas":[509,690],"austin":[636,690],"houston":[763,690],"neworleans":[890,690],"nashville":[1017,690],"miami":[1144,690],"atlanta":[1271,690]}
SHORT={'washington':'Washington','twincities':'Minneapolis'}
ABBR={'seattle':'SEA','portland':'PDX','sanfrancisco':'SF','losangeles':'LA','sandiego':'SD','lasvegas':'LV','phoenix':'PHX','denver':'DEN','austin':'ATX','dallas':'DAL','houston':'HOU','kansascity':'KC','twincities':'MSP','neworleans':'NOLA','chicago':'CHI','milwaukee':'MKE','nashville':'NASH','atlanta':'ATL','triangle':'TRI','miami':'MIA','washington':'DC','philadelphia':'PHL','newyork':'NYC','boston':'BOS','charleston':'CHS','baltimore':'BAL','detroit':'DET'}
NAMES={'charleston':'Charleston','baltimore':'Baltimore','detroit':'Detroit'}

h=open(P,encoding='utf-8').read()
# locate current stamp svg
s0=h.index('<svg viewBox="95 -170 1330 930"'); s1=h.index('</svg>',s0)+6
svg=h[s0:s1]
states=re.search(r'<g class="hp-states">.*?</g>',svg,re.S).group(0)
# extract existing stamps' image + name
IMG={}; NAME={}
for m in re.finditer(r'<g class="hp-pin"[^>]*data-city="([^"]+)"[^>]*aria-label="([^"]+)">(.*?)</g></g></g>',svg,re.S):
    city,label,inner=m.groups()
    im=re.search(r'<image href="([^"]+)"',inner)
    nm=re.search(r'<text class="hp-sp-name"[^>]*>([^<]+)</text>',inner)
    if im: IMG[city]=im.group(1)
    if nm: NAME[city]=nm.group(1)
print("extracted existing stamps:",len(IMG))
# new images
def jpg_uri(path):
    im=Image.open(path).convert("RGB")
    w=240; im=im.resize((w,round(im.height*w/im.width)))
    b=io.BytesIO(); im.save(b,"JPEG",quality=82); return "data:image/jpeg;base64,"+base64.b64encode(b.getvalue()).decode()
for c,fn in (("charleston","chs_stamp.png"),("baltimore","bal_stamp.png"),("detroit","det_stamp.png")):
    IMG[c]=jpg_uri(f"{FR}/{fn}"); NAME[c]=NAMES[c]
assert set(IMG)==set(NEW), set(IMG)^set(NEW)

out=['<svg viewBox="95 -170 1330 930" role="group" aria-label="Choose a city: stamps around the map link to each city guide">',
 '<defs><clipPath id="hp-sp-clip"><rect x="-40" y="-48" width="80" height="68"/></clipPath></defs>',states]
order=sorted(NEW, key=lambda k:k)
for n,k in enumerate(order):
    x,y=NEW[k]; sx,sy=SLOT[k]; la,lo=LATLON[k]
    rot=((n*37)%7-3)*.9
    name=NAME[k]; short=SHORT.get(k,name); label=name+" guide"; go=f"#/{k}/restaurants"
    g=[f'<g class="hp-pin" data-go="{go}" data-city="{k}" tabindex="0" role="button" aria-label="{label}">',
       f'<line class="hp-sp-lead" x1="{sx}" y1="{sy}" x2="{x}" y2="{y}"/>',
       f'<g class="hp-sp-post"><circle cx="{x}" cy="{y}" r="15"/><circle cx="{x}" cy="{y}" r="11"/>'+''.join(f'<path d="M{x+18:.1f} {y-6+j*6:.1f} q6 -4 12 0 t12 0 t12 0"/>' for j in range(3))+'</g>',
       f'<circle class="hp-sp-dot" cx="{x}" cy="{y}" r="3.6"><title>{name} ({la:.4f}, {lo:.4f})</title></circle>',
       f'<g transform="translate({sx},{sy}) rotate({rot:.1f})"><g class="hp-sp-card">',
       '<rect class="hp-sp-shadow" x="-46" y="-54" width="96" height="112"/><rect class="hp-sp-bg" x="-48" y="-56" width="96" height="112"/>']
    holes=''.join(f'<circle class="hp-sp-hole" cx="{q}" cy="-56" r="2.6"/><circle class="hp-sp-hole" cx="{q}" cy="56" r="2.6"/>' for q in range(-48,49,8))
    holes+=''.join(f'<circle class="hp-sp-hole" cx="-48" cy="{q}" r="2.6"/><circle class="hp-sp-hole" cx="48" cy="{q}" r="2.6"/>' for q in range(-48,49,8))
    g.append(holes)
    g.append(f'<image href="{IMG[k]}" x="-40" y="-48" width="80" height="68" preserveAspectRatio="xMidYMid slice" clip-path="url(#hp-sp-clip)"/>')
    g.append('<rect class="hp-sp-inner" x="-40" y="-48" width="80" height="68"/>')
    g.append(f'<text class="hp-sp-den" x="-35" y="-31" data-den="{k}"></text><text class="hp-sp-denu" x="-35" y="-23">LISTS</text>')
    g.append(f'<text class="hp-sp-name" x="0" y="38">{short}</text>')
    g.append(f'<text class="hp-sp-denu hp-sp-postage" x="0" y="49">U.S. POSTAGE · {ABBR[k]}</text>')
    g.append('</g></g></g>')
    out.append(''.join(g))
out.append('</svg>')
h=h[:s0]+''.join(out)+h[s1:]
open(P,"w",encoding='utf-8').write(h)
print("stamps regenerated: 27 cities")
