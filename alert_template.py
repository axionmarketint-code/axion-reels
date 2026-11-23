"""AXION 'Market Alert' video template (1080x1920). Fields-driven; matches the reference video.
Usage: python alert_template.py out.mp4 [json_fields]   |  from code: render_video(fields, out)"""
import json, math, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 15.0
FFMPEG = "ffmpeg"
BG=(6,11,21); CARD=(14,22,38); CARD_B=(39,53,76); PANEL=(10,17,31); PANEL_B=(37,51,74)
WATCH=(28,24,16); WATCH_B=(104,76,36); PILL=(41,15,19); PILL_B=(98,35,42)
GOLD=(244,189,64); GREEN=(64,208,144); RED=(255,77,77); WHITE=(240,244,250); GRAY=(150,163,185); GRID=(11,17,28)
import os
_H=os.path.dirname(os.path.abspath(__file__))
def _find(n):
    for p in (os.path.join(_H,"fonts",n),"/usr/share/fonts/truetype/dejavu/"+n,"C:/Windows/Fonts/verdana"+("b" if "Bold" in n else "")+".ttf","/Library/Fonts/Verdana"+(" Bold" if "Bold" in n else "")+".ttf"):
        if os.path.exists(p): return p
    return n
FB=_find("DejaVuSans-Bold.ttf"); FR=_find("DejaVuSans.ttf")
_fc={}
def font(p,s):
    k=(p,s)
    if k not in _fc: _fc[k]=ImageFont.truetype(p,s)
    return _fc[k]

DEFAULTS=dict(header="MARKET ALERT", symbol="XAUUSD", title="SHARP MOVE", subtitle="IN JUST 5 MINUTES",
  pips="+423.5", unit="PIPS", from_price="3,534", to_price="3,576",
  range_text="PRICE RANGE  •  1.7× H1 ATR", chart_label="FAST PRICE EXPANSION",
  watch_title="WHAT TO WATCH", watch1="No scheduled high-impact news nearby.",
  watch2="Possible unscheduled headline or liquidity event.",
  warn="WIDE SPREADS  •  FAST REVERSALS", advice="Don't chase the move. Stay disciplined.",
  cta="JOIN OUR FREE DAILY SETUPS", footer="ANALYSIS ONLY  •  NOT FINANCIAL ADVICE")
PTS=[(146,1185),(246,1159),(330,1170),(410,1113),(499,1130),(585,1059),(670,1080),(755,1014),(845,1030),(935,985)]

def _bgimg():
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    for x in range(0,W,90): d.line([(x,0),(x,H)],fill=GRID)
    for y in range(0,H,90): d.line([(0,y),(W,y)],fill=GRID)
    d.rectangle([0,0,W,11],fill=GOLD)
    return im
_BG=None

def txt(d,xy,s,f,fill,top=True,anchor_x="l",spacing=0.0):
    """Draw text so the glyph bbox top-left is at xy."""
    x,y=xy; l,t,r,b=f.getbbox(s)
    if anchor_x=="c": x=x-(r-l)/2
    if spacing==0: d.text((x-l,y-t),s,font=f,fill=fill); return
    for ch in s:
        d.text((x,y-t),ch,font=f,fill=fill); x+=f.getlength(ch)+spacing

def mix(a,b,k): return tuple(int(a[i]+(b[i]-a[i])*k) for i in range(3))
def ease(k): k=max(0,min(1,k)); return 1-(1-k)**3

def render_frame(F,t):
    global _BG
    if _BG is None: _BG=_bgimg()
    S=2  # supersample shapes only for the chart
    im=_BG.copy(); d=ImageDraw.Draw(im)
    # header pill + pulsing dot
    d.rounded_rectangle([65,71,1016,160],22,fill=PILL,outline=PILL_B,width=2)
    pulse=(1-math.cos(2*math.pi*t/1.25))/2
    d.ellipse([93,99,123,129],fill=mix((90,62,64),RED,pulse))
    head=f"{F['header']}  /  {F['symbol']}"
    txt(d,(148,98),head,font(FB,34),WHITE)
    # title eases in
    k=ease(t/0.6); off=int((1-k)*30)
    lay=Image.new("RGBA",(W,260),(0,0,0,0)); ld=ImageDraw.Draw(lay)
    txt(ld,(71,237-215),F["title"],font(FB,88),WHITE+(255,),spacing=-1.56)
    txt(ld,(69,329-215),F["subtitle"],font(FB,46),GOLD+(255,),spacing=0.81)
    a=lay.split()[3].point(lambda v:int(v*k)); lay.putalpha(a)
    im.paste(lay,(0,215+off),lay)
    d=ImageDraw.Draw(im)
    # main card
    d.rounded_rectangle([65,431,1016,890],30,fill=CARD,outline=CARD_B,width=2)
    txt(d,(105,482),F["symbol"],font(FB,34),GRAY)
    up=not F["pips"].strip().startswith("-"); col=GREEN if up else RED
    bf=font(FB,112); txt(d,(116,555),F["pips"],bf,col,spacing=-4)
    bw=int(sum(bf.getlength(c)-4 for c in F["pips"]))
    txt(d,(116+bw+50,603),F["unit"],font(FB,40),col,spacing=-2)
    nf=font(FB,53)
    txt(d,(108,711),F["from_price"],nf,WHITE)
    txt(d,(424,734),"→",font(FB,46),GOLD)
    txt(d,(554,711),F["to_price"],nf,WHITE)
    txt(d,(107,796),F["range_text"],font(FB,30),GOLD)
    # chart panel
    d.rounded_rectangle([111,971,969,1224],28,fill=PANEL,outline=PANEL_B,width=2)
    txt(d,(142,1000),F["chart_label"],font(FB,24),GRAY)
    for y in (1026,1091,1156): d.line([(140,y),(941,y)],fill=(32,41,54),width=2)
    pts=PTS if up else [(x,2210-y) for x,y in PTS]  # mirror for down moves
    prog=0.0 if t<2.2 else min(1,(t-2.2)/3.6)
    n=len(pts)-1; seg=prog*n
    path=[pts[0]]
    for i in range(n):
        if seg>=i+1: path.append(pts[i+1])
        elif seg>i:
            f=seg-i; x0,y0=pts[i]; x1,y1=pts[i+1]; path.append((x0+(x1-x0)*f,y0+(y1-y0)*f)); break
    if len(path)>1 or t>=0:
        ov=Image.new("RGBA",(W*1,H*1),(0,0,0,0))
        box=(100,960,980,1235); sub=Image.new("RGBA",((box[2]-box[0])*S,(box[3]-box[1])*S),(0,0,0,0)); sd=ImageDraw.Draw(sub)
        P=[((x-box[0])*S,(y-box[1])*S) for x,y in path]
        if len(P)>1: sd.line(P,fill=col+(255,),width=7*S,joint="curve")
        for p in P[:1]+P[1:]: sd.ellipse([p[0]-3.5*S,p[1]-3.5*S,p[0]+3.5*S,p[1]+3.5*S],fill=col+(255,))
        ex,ey=P[-1]; sd.ellipse([ex-12*S,ey-12*S,ex+12*S,ey+12*S],fill=col+(255,))
        sub=sub.resize((box[2]-box[0],box[3]-box[1]),Image.LANCZOS)
        im.paste(sub,(box[0],box[1]),sub)
    d=ImageDraw.Draw(im)
    # watch card
    d.rounded_rectangle([65,1281,1016,1535],30,fill=WATCH,outline=WATCH_B,width=2)
    txt(d,(106,1326),F["watch_title"],font(FB,30),GOLD)
    txt(d,(107,1385),F["watch1"],font(FR,27),WHITE)
    txt(d,(107,1430),F["watch2"],font(FR,25),GRAY)
    txt(d,(66,1598),F["warn"],font(FB,30),RED,spacing=1.17)
    txt(d,(67,1655),F["advice"],font(FR,30),WHITE)
    d.rounded_rectangle([65,1740,1016,1825],28,fill=GOLD)
    cf=font(FB,32); l,tp,r,b=cf.getbbox(F["cta"])
    d.text((540-(r-l)/2-l,1781-(tp+b)/2),F["cta"],font=cf,fill=(14,18,26))
    txt(d,(65,1865),F["footer"],font(FB,22),GRAY)
    return im

def render_video(fields,out,duration=DUR):
    F=dict(DEFAULTS); F.update({k:v for k,v in (fields or {}).items() if v not in (None,"")})
    p=subprocess.Popen([FFMPEG,"-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),
        "-i","-","-c:v","libx264","-pix_fmt","yuv420p","-preset","veryfast","-crf","20","-movflags","+faststart",out],stdin=subprocess.PIPE)
    for i in range(int(duration*FPS)): p.stdin.write(render_frame(F,i/FPS).tobytes())
    p.stdin.close(); p.wait()

# ---- parser: pull fields out of a pasted Telegram alert -------------------
def parse_alert(text):
    F={}; t=text or ""
    m=re.search(r"\b([A-Z]{3,6}(?:USD|JPY|CHF|CAD|AUD|NZD|GBP|EUR|USDT)|XAU[A-Z]{3}|XAG[A-Z]{3}|BTC[A-Z]{3,4}|ETH[A-Z]{3,4}|US30|NAS100|SPX500|GER40|USOIL|[A-Z]{3,6}/[A-Z]{3,4})\b",t)
    if m: F["symbol"]=m.group(1).replace("/","")
    m=re.search(r"([+\-−]?\s?\d[\d,]*\.?\d*)\s*(pips?|points?|pts|%)",t,re.I)
    if m:
        v=m.group(1).replace(" ","").replace("−","-"); F["pips"]=v if v[0] in "+-" else "+"+v; F["unit"]=m.group(2).upper().rstrip("S") if m.group(2).lower().startswith("pip") is False else "PIPS"
    m=re.search(r"(\d[\d,]*\.?\d*)\s*(?:→|->|-->|to)\s*(\d[\d,]*\.?\d*)",t)
    if m: F["from_price"],F["to_price"]=m.group(1),m.group(2)
    m=re.search(r"(?:in|within)\s+(?:just\s+)?(\d+)\s*(min|minutes|mins|hour|hours|h)\b",t,re.I)
    if m: F["subtitle"]=f"IN JUST {m.group(1)} "+("MINUTES" if m.group(2).lower().startswith("m") else "HOURS")
    m=re.search(r"(\d+(?:\.\d+)?)\s*[x×]\s*(H\d|M\d+|D1)?\s*ATR",t,re.I)
    if m: F["range_text"]=f"PRICE RANGE  •  {m.group(1)}× {(m.group(2) or 'H1').upper()} ATR"
    if re.search(r"sharp|spike|surge|plunge|drop",t,re.I):
        F["title"]="SHARP MOVE"
    return F

if __name__=="__main__":
    out=sys.argv[1] if len(sys.argv)>1 else "alert.mp4"
    fields=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
    render_video(fields,out)
