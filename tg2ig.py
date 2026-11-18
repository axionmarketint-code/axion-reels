#!/usr/bin/env python3
"""Telegram channel -> animated Reel -> Instagram (free, runs on GitHub Actions).

Commands
  build    read new Telegram channel posts, render one video per post,
           queue them in pending.json and write X-ready text to x_queue.md
  publish  upload the queued videos to Instagram as Reels
  demo     render a sample video locally (no network needed):
           python tg2ig.py demo "GOLD +1.2% at 2,650." out.mp4 [classic|bold|terminal|all]
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from PIL import Image, ImageDraw, ImageFont, ImageStat

# ----------------------------------------------------------------- settings
W, H, FPS = 1080, 1920, 30
ROOT = Path(__file__).resolve().parent
VIDEO_DIR = ROOT / "videos"
STATE = ROOT / "state.json"
PENDING = ROOT / "pending.json"
XQUEUE = ROOT / "x_queue.md"

BRAND = os.getenv("BRAND_NAME", "AXION")  # short name, used only if there is no logo
BRAND_FULL = os.getenv("BRAND_FULL", "AXION MARKET INTELLIGENCE")
TG_LINK = os.getenv("TELEGRAM_LINK", "t.me/AXIONMarketUpdates")
TZ = ZoneInfo(os.getenv("TIMEZONE", "America/Toronto"))
HASHTAGS = os.getenv("HASHTAGS", "#markets #trading #investing #stocks #forex")
DISCLAIMER = os.getenv(
    "DISCLAIMER", "Not financial advice. For information only. Trading involves risk."
)
MAX_POSTS_PER_RUN = int(os.getenv("MAX_POSTS_PER_RUN", "4"))
IG_HOST = os.getenv("IG_GRAPH_HOST", "https://graph.instagram.com")
IG_VERSION = os.getenv("IG_API_VERSION", "v21.0")
TEMPLATE = os.getenv("TEMPLATE", "auto")  # classic | bold | terminal | auto (rotate)
LOGO_PATH = os.getenv("LOGO_PATH") or str(ROOT / "logo.png")
LOGO_HAS_NAME = os.getenv("LOGO_HAS_NAME", "1") == "1"  # logo already shows the full name

THEMES = {
    "classic": dict(
        dark=True, bg=((8, 14, 32), (10, 60, 78)), card=(18, 28, 52), outline=None,
        text=(240, 244, 250), muted=(140, 160, 190), accent=(255, 196, 61),
        accent_text=(20, 20, 30), ticker_bg=(5, 9, 20), ticker_fg=(255, 196, 61),
        green=(46, 204, 113), red=(255, 95, 95), mono=False, typed=False,
        max_size=60, label="MARKET UPDATE",
    ),
    "bold": dict(
        dark=True, bg=((0, 0, 0), (34, 28, 4)), card=None, outline=None,
        text=(255, 255, 255), muted=(170, 160, 120), accent=(255, 214, 10),
        accent_text=(0, 0, 0), ticker_bg=(255, 214, 10), ticker_fg=(0, 0, 0),
        green=(60, 235, 130), red=(255, 85, 85), mono=False, typed=False,
        max_size=76, label="BREAKING",
    ),
    "terminal": dict(
        dark=True, bg=((2, 10, 6), (4, 30, 16)), card=(5, 18, 11), outline=(57, 255, 20),
        text=(200, 255, 215), muted=(80, 160, 100), accent=(57, 255, 20),
        accent_text=(0, 12, 4), ticker_bg=(1, 6, 3), ticker_fg=(57, 255, 20),
        green=(57, 255, 20), red=(255, 80, 80), mono=True, typed=True,
        max_size=54, label="> MARKET_UPDATE",
    ),
}


# -------------------------------------------------------------------- fonts
def font(bold, size, mono=False):
    if mono:
        names = ["DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf",
                 "LiberationMono-Bold.ttf" if bold else "LiberationMono-Regular.ttf"]
    elif bold:
        names = ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"]
    else:
        names = ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
    dirs = [
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/truetype/liberation",
        "/usr/share/fonts/dejavu",
        "/Library/Fonts",
        "C:/Windows/Fonts",
    ]
    for d in dirs:
        for n in names:
            p = Path(d) / n
            if p.exists():
                return ImageFont.truetype(str(p), size)
    if mono:
        return font(bold, size)
    return ImageFont.load_default()


# --------------------------------------------------------------------- text
URL_RE = re.compile(r"(?:https?://|t\.me/|www\.)[^\s]*[^\s.,;:!?)\]]")


DISC_RE = re.compile(
    r"not (a )?(financial|investment|trading) advice|disclaimer|risk warning|"
    r"for (informational|educational|information) (purposes )?only|trading (involves|carries)|"
    r"past performance|not a recommendation", re.I)
EMOJI_MAP = {
    "\U0001F7E2": "\u25b2", "\U0001F53A": "\u25b2", "\U0001F4C8": "\u25b2", "\u2B06": "\u25b2",
    "\U0001F534": "\u25bc", "\U0001F53B": "\u25bc", "\U0001F4C9": "\u25bc", "\u2B07": "\u25bc",
}


def strip_disclaimers(text):
    """Remove the channel's own disclaimer lines (we add a standard one)."""
    lines = [l for l in text.split("\n") if not DISC_RE.search(l)]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def clean_for_video(text):
    text = strip_disclaimers(URL_RE.sub("", text))
    for k, v in EMOJI_MAP.items():  # green/red dots -> up/down triangles
        text = text.replace(k, v)
    keep = []
    for c in text:  # fonts can't draw most emoji/symbols: drop them
        o = ord(c)
        if (o > 0xFFFF or 0x2600 <= o <= 0x27BF or 0x2B00 <= o <= 0x2BFF
                or 0x2300 <= o <= 0x23FF or o in (0xFE0F, 0x200D)):
            continue
        keep.append(c)
    text = "".join(keep)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:2500]


def word_color(word, th):
    w = word.strip("()[],;:")
    if w == "\u25b2":
        return th["green"]
    if w == "\u25bc":
        return th["red"]
    if re.search(r"\d", w):
        if w.startswith(("+", "\u25b2")):
            return th["green"]
        if w.startswith(("-", "\u2212", "\u2013", "\u25bc")) and len(w) > 1:
            return th["red"]
    u = w.upper().rstrip(".:")
    if u in ("BUY", "LONG", "BULLISH"):
        return th["green"]
    if u in ("SELL", "SHORT", "BEARISH"):
        return th["red"]
    return th["text"]


def layout(text, size, max_w, th):
    """Wrap text into lines of (word, colour, x). Blank paragraphs -> None."""
    fnt = font(True, size, th["mono"])
    space = fnt.getlength(" ")
    lines = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            lines.append(None)
            continue
        cur, x = [], 0
        for w in words:
            wl = fnt.getlength(w)
            if cur and x + wl > max_w:
                lines.append(cur)
                cur, x = [], 0
            cur.append((w, word_color(w, th), x))
            x += wl + space
        lines.append(cur)
    line_h = int(size * 1.35)
    height = sum(line_h if ln else line_h // 2 for ln in lines)
    return fnt, lines, line_h, height


# ------------------------------------------------------------------- render
def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(th):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        d.line([(0, y), (W, y)], fill=lerp(th["bg"][0], th["bg"][1], y / (H - 1)))
    return img


def centered(d, y, text, fnt, fill):
    d.text(((W - d.textlength(text, font=fnt)) / 2, y), text, font=fnt, fill=fill)


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def load_logo(th, max_w, max_h):
    """Your logo.png (transparent PNG works best). Adds a plate if it would be
    hard to see on this template's background."""
    p = Path(LOGO_PATH)
    if not p.exists():
        return None
    try:
        im = Image.open(p).convert("RGBA")
    except Exception:
        return None
    im.thumbnail((max_w, max_h), Image.LANCZOS)
    if im.split()[3].getextrema()[0] >= 250:  # logo has its own solid background
        mask = Image.new("L", im.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, im.width - 1, im.height - 1], int(min(im.size) * 0.08), fill=255
        )
        im.putalpha(mask)
        return im
    try:
        mask = im.split()[3].point(lambda v: 255 if v > 128 else 0)
        lum = ImageStat.Stat(im.convert("L"), mask=mask).mean[0]
    except Exception:
        lum = 128
    if (th["dark"] and lum < 80) or (not th["dark"] and lum > 110):
        pad = 24
        im.thumbnail((max_w - 2 * pad, max_h - 2 * pad), Image.LANCZOS)
        plate = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
        ImageDraw.Draw(plate).rounded_rectangle(
            [0, 0, plate.width - 1, plate.height - 1], 28,
            fill=(255, 255, 255, 255) if th["dark"] else (18, 28, 52, 255),
        )
        plate.alpha_composite(im, (pad, pad))
        im = plate
    return im


def draw_brand(img, th, y, logo_h, name_size):
    """Logo (or short-name pill) + full brand name. Returns the next free y."""
    d = ImageDraw.Draw(img)
    logo = load_logo(th, 900, logo_h)
    if logo:
        img.paste(logo, ((W - logo.width) // 2, y), logo)
        y += logo.height + 22
        if LOGO_HAS_NAME:
            return y
    else:
        f = font(True, 44)
        pw = d.textlength(BRAND.upper(), font=f) + 70
        d.rounded_rectangle([(W - pw) / 2, y, (W + pw) / 2, y + 80], 40, fill=th["accent"])
        centered(d, y + 13, BRAND.upper(), f, th["accent_text"])
        y += 102
    size = name_size
    f = font(True, size)
    while d.textlength(BRAND_FULL, font=f) > W - 100 and size > 24:
        size -= 2
        f = font(True, size)
    centered(d, y, BRAND_FULL, f, th["text"])
    return y + int(size * 1.5)


def paginate(text, th, max_w, min_size=46, max_h=900, max_pages=4):
    """Split long posts into pages that each fit one card at a readable size."""
    def fits(t):
        return layout(t, min_size, max_w, th)[3] <= max_h

    units = []  # (separator, text)
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block:
            continue
        if fits(block):
            units.append(("\n\n", block))
        else:  # oversize block -> split into lines
            for i, line in enumerate(l for l in block.split("\n") if l.strip()):
                units.append(("\n\n" if i == 0 else "\n", line))
    pages, cur = [], ""
    for sep, u in units:
        cand = cur + sep + u if cur else u
        if fits(cand):
            cur = cand
        else:
            if cur:
                pages.append(cur)
            cur = u
    if cur:
        pages.append(cur)
    if len(pages) > max_pages:
        pages = pages[:max_pages]
        pages[-1] += "\n\n+ more on Telegram"
    return pages or [text]


def render_video(text, when, out_path, theme_name="classic"):
    th = THEMES[theme_name]
    text = clean_for_video(text)
    if not text:
        raise ValueError("nothing to render")
    max_w, max_h = W - 220, 900
    texts = paginate(text, th, max_w)
    npages = len(texts)
    date_s = when.strftime("%b %d, %Y  |  %H:%M %Z")
    f_chip = font(True, 34)

    # ---- build every page (static scene + layout + timing)
    pages, t_acc = [], 0.0
    for pi, ptxt in enumerate(texts):
        for size in range(th["max_size"], 33, -2):
            fnt, lines, line_h, tht = layout(ptxt, size, max_w, th)
            if tht <= max_h:
                break
        words = len(ptxt.split())
        read_s = min(10.0, max(7.0 if npages == 1 else 5.0, 2.5 + words * 0.2))
        lead = 0.5 if pi == 0 else 0.0  # later pages start right away (no blank flash)
        main = gradient(th)
        d = ImageDraw.Draw(main)
        y = draw_brand(main, th, 90, 320, 40)
        cw = d.textlength(th["label"], font=f_chip) + 64
        d.rounded_rectangle([(W - cw) / 2, y, (W + cw) / 2, y + 62], 31, fill=th["accent"])
        centered(d, y + 11, th["label"], f_chip, th["accent_text"])
        y += 84
        label_date = date_s + (f"   \u2022   {pi + 1}/{npages}" if npages > 1 else "")
        centered(d, y, label_date, font(False, 30), th["muted"])
        header_bottom = y + 50
        card_h = tht + 120
        avail = (H - 260) - (header_bottom + 30)
        card_y = header_bottom + 30 + max(0, (avail - card_h) // 2)
        card = (60, card_y, W - 60, card_y + card_h)
        if th["card"]:
            d.rounded_rectangle(card, 36, fill=th["card"], outline=th["outline"], width=3)
        d.rounded_rectangle([card[0], card[1], card[0] + 14, card[3]], 7, fill=th["accent"])
        d.rectangle([0, H - 170, W, H], fill=th["ticker_bg"])
        centered(d, H - 225, DISCLAIMER[:75], font(False, 26), th["muted"])

        starts, i = [], 0
        for ln in lines:
            starts.append(lead + 0.38 * i)
            if ln:
                i += 1
        last_start = starts[-1] if starts else lead
        if last_start > read_s * 0.6:
            scale = (read_s * 0.6 - lead) / max(0.1, last_start - lead)
            starts = [lead + (s_ - lead) * scale for s_ in starts]
        total_chars = sum(len(w) + 1 for ln in lines if ln for w, _, _ in ln)
        pages.append(dict(
            main=main, fnt=fnt, lines=lines, line_h=line_h, size=size, card=card,
            read_s=read_s, t0=t_acc, starts=starts, lead=lead,
            cps=max(28.0, total_chars / (read_s * 0.55)),
        ))
        t_acc += read_s
    pages_dur = t_acc
    total = pages_dur + 3.0

    fade_base = lambda yy: th["card"] or lerp(th["bg"][0], th["bg"][1], yy / (H - 1))

    def draw_page(frame, pg, tl):
        fd = ImageDraw.Draw(frame)
        fnt, lines, line_h, size, card = pg["fnt"], pg["lines"], pg["line_h"], pg["size"], pg["card"]
        x0, y = card[0] + 50, card[1] + 60
        if th["typed"]:
            budget = int(max(0, tl - pg["lead"]) * pg["cps"])
            cur_pos = (x0, y)
            for ln in lines:
                if not ln:
                    y += line_h // 2
                    continue
                for w, col, wx in ln:
                    if budget <= 0:
                        break
                    part = w[:budget]
                    budget -= len(w) + 1
                    fd.text((x0 + wx, y), part, font=fnt, fill=col)
                    cur_pos = (x0 + wx + fnt.getlength(part) + 6, y)
                y += line_h
            if int(tl * 2) % 2 == 0:
                cx, cy = cur_pos
                fd.rectangle([cx, cy + 6, cx + int(size * 0.5), cy + int(size * 1.1)], fill=th["accent"])
        else:
            for ln, st in zip(lines, pg["starts"]):
                if not ln:
                    y += line_h // 2
                    continue
                a = ease((tl - st) / 0.45)
                if a > 0:
                    slide = int((1 - a) * 24)
                    base = fade_base(y)
                    for w, col, wx in ln:
                        fd.text((x0 + wx, y + slide), w, font=fnt, fill=lerp(base, col, a))
                y += line_h

    # ---- static end card
    end = gradient(th)
    e = ImageDraw.Draw(end)
    y2 = draw_brand(end, th, 190, 480, 44)
    centered(e, y2 + 90, "Want every update", font(True, 70), th["text"])
    centered(e, y2 + 180, "the moment it drops?", font(True, 70), th["text"])
    by = y2 + 330
    e.rounded_rectangle([90, by, W - 90, by + 200], 44, fill=th["accent"])
    centered(e, by + 30, "JOIN FREE ON TELEGRAM", font(True, 46), th["accent_text"])
    centered(e, by + 105, TG_LINK, font(True, 50), th["accent_text"])
    centered(e, by + 250, "Link in bio", font(False, 40), th["muted"])
    f_small = font(False, 28)
    dl, cur = [], ""
    for w in DISCLAIMER.split():
        if f_small.getlength(cur + " " + w) > W - 160 and cur:
            dl.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    dl.append(cur)
    for i, ln in enumerate(dl):
        centered(e, 1560 + i * 40, ln, f_small, th["muted"])
    fin = pages[-1]["main"].copy()
    draw_page(fin, pages[-1], 999)

    # ---- ticker strip
    ticker_txt = f"   {BRAND_FULL}   \u2022   JOIN FREE: {TG_LINK}   \u2022   LIVE MARKET UPDATES   \u2022"
    f_tick = font(True, 40)
    unit = f_tick.getlength(ticker_txt)
    speed = 170
    strip_w = int(speed * total + W + unit * 2)
    strip = Image.new("RGB", (strip_w, 100), th["ticker_bg"])
    sd = ImageDraw.Draw(strip)
    x = 0
    while x < strip_w:
        sd.text((x, 28), ticker_txt, font=f_tick, fill=th["ticker_fg"])
        x += unit

    VIDEO_DIR.mkdir(exist_ok=True)
    n = int(total * FPS)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", f"{total:.2f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart",
        str(out_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(n):
        t = fi / FPS
        if t >= pages_dur + 0.5:
            a = ease((t - (pages_dur + 0.5)) / 0.5)
            frame = Image.blend(fin, end, a) if a < 1 else end.copy()
        else:
            pg = pages[0]
            for cand in pages:
                if cand["t0"] <= t:
                    pg = cand
            frame = pg["main"].copy()
            draw_page(frame, pg, t - pg["t0"])
            ImageDraw.Draw(frame).rectangle([0, 0, int(W * min(1, t / pages_dur)), 10], fill=th["accent"])
        off = int(t * speed)
        frame.paste(strip.crop((off, 0, off + W, 100)), (0, H - 135))
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed")
    return total


# ------------------------------------------------------------- state helpers
def load_json(path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))


def need(name):
    v = os.getenv(name)
    if not v:
        sys.exit(f"Missing required setting: {name}")
    return v


def http(method, url, **kw):
    """requests wrapper that never leaks URLs/tokens into error output."""
    try:
        return requests.request(method, url, timeout=60, **kw)
    except requests.RequestException as e:
        raise RuntimeError(f"Network error ({type(e).__name__})") from None


# ------------------------------------------------------------------- build
def make_x_text(text):
    body = strip_disclaimers(URL_RE.sub("", text))
    body = re.sub(r"\n{3,}", "\n\n", body)
    room = 280 - 23 - 4  # X counts any link as 23 characters
    if len(body) > room:
        out = ""
        for line in body.split("\n"):
            nxt = out + ("\n" if out else "") + line
            if len(nxt) > room - 2:
                break
            out = nxt
        body = (out or body[: room - 3].rsplit(" ", 1)[0]) + " ..."
    return f"{body}\n\nFull update: {TG_LINK}"


def cmd_build():
    token = need("TELEGRAM_BOT_TOKEN")
    channel = os.getenv("TELEGRAM_CHANNEL_ID", "").strip()
    state = load_json(STATE, {"offset": 0})
    pending = load_json(PENDING, [])

    r = http(
        "GET",
        f"https://api.telegram.org/bot{token}/getUpdates",
        params={
            "offset": state["offset"],
            "timeout": 0,
            "allowed_updates": json.dumps(["channel_post"]),
        },
    )
    data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    if r.status_code != 200 or not data.get("ok"):
        sys.exit(f"Telegram error {r.status_code}: {data.get('description', 'unknown')}")
    updates = data["result"]

    if not state.get("initialized") and os.getenv("BACKFILL") != "1":
        if updates:
            state["offset"] = updates[-1]["update_id"] + 1
        state["initialized"] = True
        save_json(STATE, state)
        print(f"First run: skipped {len(updates)} older posts. New posts will be processed from now on.")
        return

    done = 0
    for u in updates:
        if done >= MAX_POSTS_PER_RUN:
            break  # leave the rest for the next run
        state["offset"] = u["update_id"] + 1
        post = u.get("channel_post")
        if not post:
            continue
        chat = post.get("chat", {})
        if channel and channel.lstrip("@").lower() not in (
            str(chat.get("id")), (chat.get("username") or "").lower()
        ):
            continue
        text = post.get("text") or post.get("caption") or ""
        if not text.strip():
            continue

        when = datetime.fromtimestamp(post["date"], TZ)
        names = list(THEMES)
        if TEMPLATE in THEMES:
            tpl = TEMPLATE
        else:  # "auto": rotate through all templates
            tpl = names[state.get("n", 0) % len(names)]
            state["n"] = state.get("n", 0) + 1
        vid = f"{post['chat']['id']}_{post['message_id']}".replace("-", "n")
        path = VIDEO_DIR / f"{vid}.mp4"
        try:
            secs = render_video(text, when, path, tpl)
        except Exception as e:  # keep going if one post fails
            print(f"Could not render post {post['message_id']}: {e}")
            continue
        print(f"Rendered {path.name} ({secs:.1f}s, template: {tpl})")

        caption = (
            f"{strip_disclaimers(URL_RE.sub('', text))[:1500]}\n\n"
            f"Join free on Telegram (link in bio): {TG_LINK}\n\n"
            f"{DISCLAIMER}\n\n{BRAND_FULL}\n{HASHTAGS}"
        )[:2200]
        pending.append({"file": path.name, "caption": caption, "attempts": 0})
        with XQUEUE.open("a", encoding="utf-8") as f:
            f.write(f"### {when.strftime('%Y-%m-%d %H:%M')}\n```\n{make_x_text(text)}\n```\n\n")
        done += 1

    state["initialized"] = True
    save_json(STATE, state)
    save_json(PENDING, pending)
    print(f"Queued {done} new post(s).")


# ----------------------------------------------------------------- publish
def ig_call(method, path, token, **kw):
    r = http(
        method,
        f"{IG_HOST}/{IG_VERSION}/{path}",
        headers={"Authorization": f"Bearer {token}"},
        **kw,
    )
    try:
        j = r.json()
    except ValueError:
        j = {}
    if r.status_code != 200:
        err = j.get("error", {})
        raise RuntimeError(f"Instagram error {r.status_code}: {err.get('message', 'unknown')}")
    return j


def ig_publish_reel(user_id, token, video_url, caption):
    c = ig_call(
        "POST", f"{user_id}/media", token,
        data={"media_type": "REELS", "video_url": video_url,
              "caption": caption, "share_to_feed": "true"},
    )["id"]
    for _ in range(40):  # up to ~7 minutes
        s = ig_call("GET", c, token, params={"fields": "status_code,status"})
        code = s.get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram could not process the video: {s.get('status')}")
        time.sleep(10)
    else:
        raise RuntimeError("Timed out waiting for Instagram to process the video")
    return ig_call("POST", f"{user_id}/media_publish", token, data={"creation_id": c})["id"]


def cmd_publish():
    pending = load_json(PENDING, [])
    if not pending:
        print("Nothing to publish.")
        return
    user_id, token = os.getenv("IG_USER_ID"), os.getenv("IG_ACCESS_TOKEN")
    base = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    if not (user_id and token and base):
        print("Instagram not configured yet - skipping videos (X text is still saved).")
        for p in pending:
            (VIDEO_DIR / p["file"]).unlink(missing_ok=True)
        save_json(PENDING, [])
        return

    keep = []
    for p in pending:
        url = f"{base}/{p['file']}"
        try:
            for _ in range(8):  # wait for GitHub's CDN to serve the new file
                if http("HEAD", url).status_code == 200:
                    break
                time.sleep(10)
            else:
                raise RuntimeError("Video URL not reachable (is the repo public?)")
            media_id = ig_publish_reel(user_id, token, url, p["caption"])
            print(f"Published {p['file']} -> Instagram media {media_id}")
            (VIDEO_DIR / p["file"]).unlink(missing_ok=True)
        except Exception as e:
            p["attempts"] += 1
            print(f"Failed {p['file']} (attempt {p['attempts']}): {e}")
            if p["attempts"] < 3:
                keep.append(p)
            else:
                (VIDEO_DIR / p["file"]).unlink(missing_ok=True)
    save_json(PENDING, keep)


# -------------------------------------------------------------------- main
def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "build":
        cmd_build()
    elif cmd == "publish":
        cmd_publish()
    elif cmd == "demo":
        text = sys.argv[2] if len(sys.argv) > 2 else "GOLD +1.2% at 2,650. Support 2,620."
        out = Path(sys.argv[3] if len(sys.argv) > 3 else "demo.mp4")
        tpl = sys.argv[4] if len(sys.argv) > 4 else "classic"
        for name in (list(THEMES) if tpl == "all" else [tpl]):
            o = out.with_name(f"{out.stem}_{name}.mp4") if tpl == "all" else out
            print(f"Rendered {o} ({render_video(text, datetime.now(TZ), o, name):.1f}s)")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
