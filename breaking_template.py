"""AXION 'Breaking News' video template (1080x1920) built from the user's own artwork (assets/breaking_news_art.jpg)."""
import json, math, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, DUR = 1080, 1920, 30, 12.0
FFMPEG = "ffmpeg"
_H = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(_H, "assets", "breaking_news_art.jpg")
def _font(n):
    for p in (os.path.join(_H, "fonts", n), "/usr/share/fonts/truetype/dejavu/" + n):
        if os.path.exists(p): return p
    return n
SB, SR_ = _font("DejaVuSerif-Bold.ttf"), _font("DejaVuSerif.ttf")
_fc = {}
def font(p, s):
    if (p, s) not in _fc: _fc[(p, s)] = ImageFont.truetype(p, s)
    return _fc[(p, s)]

GOLD_HI, GOLD_MID, GOLD_LO = (255, 236, 168), (219, 170, 62), (128, 88, 26)
DEFAULTS = dict(tag="MARKET NEWS", headline="US CPI COMES IN HOTTER THAN EXPECTED",
    body="Inflation rose 0.4% on the month, above the 0.3% forecast. Treasury yields jumped and the dollar strengthened across the board.",
    stats=["ACTUAL|3.4%", "FORECAST|3.2%", "PREVIOUS|3.1%"], stamp="",
    disclaimer1="Educational content only. Not investment or financial advice.",
    disclaimer2="You are responsible for your own trading decisions.")

_assets = {}
def assets():
    if _assets: return _assets
    art = Image.open(ART).convert("RGB")
    # marble texture: free area of the art, mirrored-tiled to fill the canvas
    m = art.crop((0, 300, 1376, 505)).crop((148, 0, 148 + 1080, 205))
    tile = Image.new("RGB", (1080, 410)); tile.paste(m, (0, 0)); tile.paste(m.transpose(Image.FLIP_TOP_BOTTOM), (0, 205))
    bg = Image.new("RGB", (W, 410 * 5))
    for i in range(5): bg.paste(tile if i % 2 == 0 else tile.transpose(Image.FLIP_TOP_BOTTOM), (0, i * 410))
    bg = bg.crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(1.2))
    a = np.asarray(bg).astype(float)
    yy = np.linspace(0, 1, H)[:, None, None]; xx = np.linspace(-1, 1, W)[None, :, None]
    a *= 0.55 + 0.45 * (1 - 0.6 * np.abs(xx) ** 2) * (1 - 0.25 * np.abs(yy - .5))
    _assets["bg"] = Image.fromarray(np.clip(a, 0, 255).astype("uint8"))
    ban = art.crop((0, 40, 1376, 300)); sc = W / 1376
    ban = ban.resize((W, int(260 * sc)), Image.LANCZOS).convert("RGBA")
    h_ = ban.height; al = np.ones((h_, W)); fade = 34
    al[:fade] *= np.linspace(0, 1, fade)[:, None]; al[-fade:] *= np.linspace(1, 0, fade)[:, None]
    ban.putalpha(Image.fromarray((al * 255).astype("uint8"))); _assets["banner"] = ban
    tabs = art.crop((868, 514, 1212, 568)); _assets["tabs"] = tabs.resize((int(344 * .95), int(54 * .95)), Image.LANCZOS)
    _assets["panel_tex"] = art.crop((0, 300, 1376, 505))
    return _assets

def gold_text(img, xy, s, f, anchor="l", shimmer=None, alpha=1.0, shadow=True):
    """Gold-gradient text with a dark drop shadow. xy = (x, top of glyph box)."""
    l, t, r, b = f.getbbox(s); w, h = r - l + 8, b - t + 8
    x, y = xy
    if anchor == "c": x -= (r - l) / 2
    mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).text((4 - l, 4 - t), s, font=f, fill=255)
    g = np.zeros((h, w, 3)); ys = np.linspace(0, 1, h)[:, None]
    for i in range(3):
        top, mid, lo = GOLD_HI[i], GOLD_MID[i], GOLD_LO[i]
        g[..., i] = np.where(ys < .5, top + (mid - top) * ys * 2, mid + (lo - mid) * (ys - .5) * 2)
    if shimmer is not None:
        xs = np.arange(w)[None, :]; d = np.abs(xs - shimmer * (w + 300) + 150); k = np.clip(1 - d / 90, 0, 1)[..., None]
        g = g + (255 - g) * 0.7 * k
    col = Image.fromarray(np.clip(g, 0, 255).astype("uint8"))
    if alpha < 1: mask = mask.point(lambda v: int(v * alpha))
    if shadow:
        sh = Image.new("L", (w, h), 0); sh.paste(mask, (3, 4)); sh = sh.filter(ImageFilter.GaussianBlur(2))
        img.paste(Image.new("RGB", (w, h), (0, 0, 0)), (int(x) - 4, int(y) - 4), sh.point(lambda v: int(v * .8)))
    img.paste(col, (int(x) - 4, int(y) - 4), mask)

def wrap(s, f, maxw):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if f.getlength(t) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = wd
    if cur: lines.append(cur)
    return lines

def fit_headline(s, maxw, maxlines=4):
    for lim in (3, maxlines):  # prefer 3 lines at a still-large size, then allow more
        for size in range(96, 59 if lim == 3 else 40, -4):
            f = font(SB, size); ls = wrap(s.upper(), f, maxw)
            if len(ls) <= lim and all(f.getlength(l) <= maxw for l in ls): return f, ls
    f = font(SB, 40); return f, wrap(s.upper(), f, maxw)[:maxlines]

def ease(k): k = max(0, min(1, k)); return 1 - (1 - k) ** 3

def gold_frame(d, box, r=16, w=4):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, r, outline=GOLD_MID, width=w)
    d.rounded_rectangle((x0 + w, y0 + w, x1 - w, y1 - w), r - 3, outline=GOLD_HI, width=1)
    d.rounded_rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), r + 2, outline=GOLD_LO, width=2)

def render_frame(F, t):
    A = assets(); img = A["bg"].copy(); d = ImageDraw.Draw(img)
    # top banner slides in from the left
    hf, lines = fit_headline(F["headline"], W - 180)
    lh = int(hf.size * 1.22); ph = lh * len(lines) + 90
    bf = font(SR_, 38); body = wrap(F["body"], bf, W - 140)[:6]
    stats = [s.split("|", 1) for s in F["stats"] if "|" in s][:3]
    total = A["banner"].height + 60 + 70 + ph + 50 + len(body) * 56 + 40 + (190 if stats else 0) + (50 if F.get("stamp") else 0)
    y0 = 110 + max(0, int((H - 150 - 110 - total) * 0.45))
    k = ease(t / 0.7); bx = int(-W * (1 - k)); img.paste(A["banner"], (bx, y0), A["banner"])
    y = y0 + A["banner"].height + 60
    # tab + icon strip
    k = ease((t - .5) / .5)
    if k > 0:
        tag = F["tag"].upper(); tf = font(SB, 34); tw = int(tf.getlength(tag)) + 56
        tl = Image.new("RGBA", (tw, 62), (0, 0, 0, 0)); td = ImageDraw.Draw(tl)
        td.rounded_rectangle((0, 0, tw - 1, 80), 14, fill=(205, 160, 62, 255)); td.rounded_rectangle((3, 3, tw - 4, 80), 12, outline=(255, 232, 160, 255), width=2)
        td.text((28, 11), tag, font=tf, fill=(30, 22, 8, 255))
        tl.putalpha(tl.split()[3].point(lambda v: int(v * k))); img.paste(tl, (40, y), tl)
        ti = A["tabs"].copy(); img.paste(ti, (W - 40 - ti.width, y + 8))
    y += 70
    # headline panel
    k = ease((t - .8) / .7)
    if k > 0:
        pnl = Image.new("RGB", (W - 80, ph)); tex = A["panel_tex"].resize((W - 80, ph)).point(lambda v: int(v * .8)); pnl.paste(tex)
        full = Image.new("L", pnl.size, 0); ImageDraw.Draw(full).rounded_rectangle((0, 0, pnl.width - 1, int(ph * k)), 20, fill=255)
        img.paste(pnl, (40, y), full)
        gold_frame(d, (40, y, W - 41, y + int(ph * k)), 20)
    # headline lines, typed in one after another with a gold shimmer
    for i, ln in enumerate(lines):
        kk = ease((t - 1.3 - i * .35) / .5)
        if kk <= 0: continue
        ph_t = (t % 6) / 1.4 - 0.3 - i * .1
        gold_text(img, (W / 2, y + 45 + i * lh + (1 - kk) * 24), ln, hf, "c", shimmer=ph_t if 0 <= ph_t <= 1 else None, alpha=kk)
    y += ph + 50
    # body text
    for i, ln in enumerate(body):
        kk = ease((t - 2.6 - i * .15) / .5)
        if kk > 0:
            c = tuple(int(240 * kk + 10 * (1 - kk)) for _ in range(3)); d.text((70, y + i * 56 + (1 - kk) * 14), ln, font=bf, fill=c)
    y += len(body) * 56 + 40
    # stat boxes
    if stats:
        bw = (W - 80 - 20 * (len(stats) - 1)) // len(stats)
        for i, (lab, val) in enumerate(stats):
            kk = ease((t - 4.0 - i * .25) / .5)
            if kk <= 0: continue
            x0 = 40 + i * (bw + 20); yy = y + int((1 - kk) * 30)
            box = Image.new("RGB", (bw, 150)); box.paste(A["panel_tex"].resize((bw, 150)).point(lambda v: int(v * .8)))
            m = Image.new("L", (bw, 150), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, bw - 1, 149), 14, fill=int(255 * kk)); img.paste(box, (x0, yy), m)
            gold_frame(d, (x0, yy, x0 + bw - 1, yy + 149), 14, 3)
            lf = font(SB, 24); lw = lf.getlength(lab.upper()); d.text((x0 + (bw - lw) / 2, yy + 20), lab.upper(), font=lf, fill=(200, 170, 100))
            gold_text(img, (x0 + bw / 2, yy + 62), val, font(SB, 54), "c", alpha=kk)
        y += 190
    if F.get("stamp"):
        sf = font(SB, 28); sw = sf.getlength(F["stamp"].upper()); d.text(((W - sw) / 2, y + 10), F["stamp"].upper(), font=sf, fill=(205, 165, 70))
    # disclaimer bar
    d.rectangle((0, H - 150, W, H), fill=(10, 9, 7)); d.line((0, H - 150, W, H - 150), fill=GOLD_MID, width=3)
    df = font(SR_, 25); lab = "Disclaimer: "; lw = font(SB, 25).getlength(lab); l1 = F["disclaimer1"]
    tw = lw + df.getlength(l1); x = (W - tw) / 2
    d.text((x, H - 118), lab, font=font(SB, 25), fill=(225, 180, 80)); d.text((x + lw, H - 118), l1, font=df, fill=(235, 235, 235))
    d.text(((W - df.getlength(F["disclaimer2"])) / 2, H - 76), F["disclaimer2"], font=df, fill=(235, 235, 235))
    return img

def render_video(fields, out, duration=DUR):
    F = dict(DEFAULTS); F.update({k: v for k, v in (fields or {}).items() if v not in (None, "")})
    p = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(int(duration * FPS)): p.stdin.write(render_frame(F, i / FPS).tobytes())
    p.stdin.close(); p.wait()

def parse_news(text):
    """First line (or sentence) becomes the headline, the rest the body; 'Label: value' lines become stat boxes."""
    t = re.sub(r"[\U0001F000-\U0001FFFF☀-➿]", "", text or "").strip()
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    F = {}; stats = []; rest = []
    for l in lines:
        m = re.match(r"^(actual|forecast|previous|consensus|prior|expected)\s*[:\-]\s*(.+)$", l, re.I)
        if m: stats.append(f"{m.group(1).upper()}|{m.group(2).strip()}")
        else: rest.append(l)
    if rest:
        head = re.sub(r"^(breaking( news)?|urgent|news result|news)\s*[:\-–—]*\s*", "", rest[0], flags=re.I).strip() or rest[0]
        F["headline"] = head[:110]; F["body"] = " ".join(rest[1:])[:300] or ""
    if stats: F["stats"] = stats[:3]
    else: F["stats"] = []
    return F

if __name__ == "__main__":
    render_video(json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}, sys.argv[1] if len(sys.argv) > 1 else "breaking.mp4")
