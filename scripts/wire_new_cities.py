#!/usr/bin/env python3
"""Wire Charleston/Baltimore/Detroit into index.html: assets, CITYMETA, NAME, tiers, banners, selector."""
import re, base64, io, json
from PIL import Image
AT="/mnt/user-data/attachments/3bad3a39-e70c-5398-88c1-48d74ebf8e65"
P="/home/claude/bestofthebest/index.html"

# city -> (skyline png, nameplate png, video mp4, video WxH, banner prefix)
A={
 "charleston":("88232327-image.png","20cada61-image.png","beaf0baa-Charleston_Neon_8s_Bulbs_Corrected.mp4","2172/724","chs"),
 "baltimore":("104d679e-image.png","89b4e70f-image.png","dd1eefc4-Baltimore_Neon_Harbor_No_Box_Shimmer_Cranes_8s.mp4","1984/794","bal"),
 "detroit":("65f524c9-image.png","ee4e3e47-image.png","c96eaad5-Detroit_Neon_8s_Seamless_Loop_2560x432.mp4","2560/432","det"),
}

def png_b64(im):
    b=io.BytesIO(); im.save(b,"PNG",optimize=True); return base64.b64encode(b.getvalue()).decode()

def sky_uri(path):
    im=Image.open(path).convert("L")
    w=1100; im=im.resize((w,round(im.height*w/im.width)))
    return "data:image/png;base64,"+png_b64(im)

def np_uri(path):
    im=Image.open(path).convert("RGBA")
    bbox=im.getchannel("A").getbbox()
    if bbox: im=im.crop(bbox)
    w=1300
    if im.width>w: im=im.resize((w,round(im.height*w/im.width)))
    return "data:image/png;base64,"+png_b64(im)

def vid_uri(path):
    return "data:video/mp4;base64,"+base64.b64encode(open(path,"rb").read()).decode()

meta={}
for city,(sky,np,vid,ar,pfx) in A.items():
    meta[city]=dict(
        np=np_uri(f"{AT}/{np}"), sky=sky_uri(f"{AT}/{sky}"),
        vid=vid_uri(f"{AT}/{vid}"), ar=ar, pfx=pfx)
    print(f"{city}: np+sky+vid encoded, ar={ar}")

h=open(P,encoding="utf-8").read()
orig=len(h)

# 1) NAME keys
anchor='NAME["twincities"]="Minneapolis";'
assert h.count(anchor)==1
h=h.replace(anchor, anchor+'NAME["charleston"]="Charleston";NAME["baltimore"]="Baltimore";NAME["detroit"]="Detroit";')

# 2) CITYMETA entries (insert right after 'const CITYMETA={')
cm_anchor='const CITYMETA={'
entries=""
for city in A:
    m=meta[city]
    entries+=('"%s": {"np": {"type":"img","uri":"%s"}, "sky": {"uri":"%s","w":"min(690px,92vw)","h":"230px","bottom":"-13px"}}, '
              %(city,m["np"],m["sky"]))
h=h.replace(cm_anchor, cm_anchor+entries, 1)

# 3) restoTiers map
rt_anchor='denver:[S,DN,TA,IT,AS,WT]\n  };'
assert h.count(rt_anchor)==1
rt_new=('denver:[S,DN,TA,IT,AS,WT],\n'
        '    charleston:[S,BBQ,DN,TA,IT,AS,OG,QB,BR,WT],\n'
        '    baltimore:[S,DN,IT,TA,AS,OG,QB,BR,WT],\n'
        '    detroit:[S,DN,TA,IT,AS,OG,QB,BR,WT]\n  };')
h=h.replace(rt_anchor, rt_new)

# 4) barTiers brewery for charleston
bt_anchor='if(city==="boston"||city==="denver") arr.push(["brewery"'
assert h.count(bt_anchor)==1
h=h.replace(bt_anchor,'if(city==="boston"||city==="denver"||city==="charleston") arr.push(["brewery"')

# 5) Banner CSS (append after den-banner cluster)
css_anchor='body.city-denver.theme-bars .mast-center{visibility:hidden;}\n'
assert h.count(css_anchor)==1
css=""
for city,(sky,np,vid,ar,pfx) in A.items():
    css+=(
      f".{pfx}-banner{{display:none;position:absolute;inset:0;z-index:1;overflow:hidden;}}\n"
      f"  body.city-{city}.theme-bars .{pfx}-banner{{display:block;}}\n"
      f"  body.city-{city}.theme-bars .mast-center{{visibility:hidden;}}\n"
      f"  .{pfx}-stage{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);height:100%;aspect-ratio:{ar};max-width:100%;overflow:hidden;}}\n"
      f"  .{pfx}-vid{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center center;display:block;"
      f"-webkit-mask-image:linear-gradient(90deg,transparent 0,#000 16%,#000 84%,transparent 100%);mask-image:linear-gradient(90deg,transparent 0,#000 16%,#000 84%,transparent 100%);}}\n  ")
h=h.replace(css_anchor, css_anchor+css)

# 6) Banner markup (insert before la-banner div)
dom_anchor='<div class="la-banner" aria-hidden="true">'
assert h.count(dom_anchor)==1
markup=""
for city,(sky,np,vid,ar,pfx) in A.items():
    markup+=(f'<div class="{pfx}-banner" aria-hidden="true"><div class="{pfx}-stage">'
             f'<video class="{pfx}-vid" muted loop playsinline autoplay preload="auto">'
             f'<source src="{meta[city]["vid"]}" type="video/mp4"></video></div></div>\n  ')
h=h.replace(dom_anchor, markup+dom_anchor)

# 7) City selector buttons (alphabetical)
def btn(city,name): return f'<button class="city-btn" data-city="{city}">{name}</button>'
ins=[('data-city="austin">Austin</button>', btn("baltimore","Baltimore")),   # Baltimore after Austin
     ('data-city="boston">Boston</button>', btn("charleston","Charleston")),  # Charleston after Boston
     ('data-city="denver">Denver</button>', btn("detroit","Detroit"))]        # Detroit after Denver
for anc,b in ins:
    assert h.count(anc)==1, anc
    h=h.replace(anc, anc+b)

open(P,"w",encoding="utf-8").write(h)
print(f"index.html wired: {orig} -> {len(h)} bytes (+{len(h)-orig})")
