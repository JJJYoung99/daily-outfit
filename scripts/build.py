#!/usr/bin/env python3
"""Build the outfit pages from days/<YYYY-MM-DD>/day.json.

day.json outfits list item ids from closet/closet.json; this script composes each outfit
image from closet/items/<id>.jpg and writes docs/index.html + docs/archive/<date>.html.
"""
import html, json, pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
DAYS, DOCS = ROOT / "days", ROOT / "docs"
ITEMS = ROOT / "closet" / "items"
CLOSET = {c["id"]: c for c in json.loads((ROOT / "closet" / "closet.json").read_text(encoding="utf-8"))}
PART = {"top": "상의", "bottom": "하의", "outer": "아우터", "shoes": "신발", "acc": "가방·액세서리"}
W, H = 1100, 1300


def e(s):
    return html.escape(str(s or ""))


def paste_fit(canvas, img, box):
    x0, y0, x1, y1 = box
    k = min((x1 - x0) / img.width, (y1 - y0) / img.height)
    im = img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))), Image.LANCZOS)
    canvas.paste(im, (x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2))


def compose(item_ids, out_path):
    by = {"top": [], "bottom": [], "outer": [], "shoes": [], "acc": []}
    for i in item_ids:
        by[CLOSET[i]["cat"]].append(Image.open(ITEMS / f"{i}.jpg").convert("RGB"))
    c = Image.new("RGB", (W, H), "white")
    tops, outer = by["top"][:2], by["outer"][:1]
    if outer:
        top_boxes = [(40, 40, 520, 600)] if len(tops) == 1 else [(20, 40, 300, 560), (290, 80, 560, 600)]
        paste_fit(c, outer[0], (560, 30, 1080, 780))
        acc_boxes = [(600, 790, 820, 950), (840, 790, 1060, 950)]
        shoe_box = (620, 960, 1060, 1260)
    else:
        top_boxes = [(300, 30, 800, 600)] if len(tops) == 1 else [(60, 40, 520, 600), (560, 40, 1040, 600)]
        acc_boxes = [(600, 640, 820, 860), (840, 640, 1060, 860)]
        shoe_box = (600, 900, 1060, 1260)
    for img, box in zip(tops, top_boxes):
        paste_fit(c, img, box)
    if by["bottom"]:
        paste_fit(c, by["bottom"][0], (60, 620, 520, 1270))
    if by["shoes"]:
        paste_fit(c, by["shoes"][0], shoe_box)
    for img, box in zip(by["acc"][:2], acc_boxes):
        paste_fit(c, img, box)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c.save(out_path, quality=85, optimize=True)


def load_days():
    out = []
    for d in sorted(DAYS.iterdir(), reverse=True):
        f = d / "day.json"
        if f.exists():
            out.append(json.loads(f.read_text(encoding="utf-8")))
    return out


def fmt_date(iso, wd):
    _, m, d = iso.split("-")
    return f"{int(m)}월 {int(d)}일 ({wd})"


CSS = """
:root { --bg:#f3f4f2; --surface:#fff; --fg:#1d201f; --muted:#6a706d; --line:#dfe2df; --accent:#3d5a6c; --accent-soft:#e3eaee; --rain:#2f6f9f;
  --sans:"IBM Plex Sans KR","Apple SD Gothic Neo",system-ui,sans-serif; --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace; color-scheme:light; }
@media (prefers-color-scheme: dark) { :root { --bg:#151817; --surface:#1e2221; --fg:#e8ebe9; --muted:#9aa19e; --line:#2e3432; --accent:#9cbccf; --accent-soft:#24313a; --rain:#7fb6e0; color-scheme:dark; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font-family:var(--sans); font-size:15px; line-height:1.6;
  padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)); padding-block:28px 48px; }
a { color:inherit; }
.wrap { max-width:980px; margin:0 auto; display:flex; flex-direction:column; gap:28px; }
header { display:flex; flex-direction:column; gap:6px; }
.eyebrow { font-size:12px; letter-spacing:.08em; color:var(--muted); }
h1 { font-size:clamp(26px,5vw,36px); line-height:1.2; margin:0; text-wrap:balance; }
h2 { font-size:15px; margin:0; color:var(--muted); font-weight:500; letter-spacing:.04em; }
.ribbon { display:flex; flex-wrap:wrap; gap:8px; }
.chip { display:inline-flex; gap:6px; align-items:baseline; padding:6px 12px; border-radius:999px; background:var(--surface); border:1px solid var(--line); font-size:13px; }
.chip b { font-family:var(--mono); font-weight:500; font-variant-numeric:tabular-nums; }
.chip.rain b { color:var(--rain); }
.chip.tpo { background:var(--accent-soft); border-color:transparent; color:var(--accent); font-weight:500; }
.note { margin:0; color:var(--muted); max-width:65ch; }
.outfit { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:24px; align-items:start; }
.outfit.main { background:var(--surface); border:1px solid var(--line); border-radius:16px; padding:20px; }
.outfit.sub { grid-template-columns:minmax(0,220px) minmax(0,1fr); padding:0 4px; }
figure { margin:0; }
.outfit img { width:100%; aspect-ratio:1100/1300; object-fit:contain; border-radius:12px; background:#fff; display:block; }
.desc { display:flex; flex-direction:column; gap:12px; min-width:0; }
.otitle { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
h3 { margin:0; font-size:20px; line-height:1.3; }
.sub h3 { font-size:17px; }
.badge { font-size:12px; font-weight:700; padding:2px 10px; border-radius:999px; background:var(--accent); color:var(--bg); }
.badge.alt { background:transparent; color:var(--muted); border:1px solid var(--line); }
.why { margin:0; }
.items { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; }
.items li { display:grid; grid-template-columns:76px minmax(0,1fr); gap:12px; padding:10px 0; border-top:1px solid var(--line); }
.items li p { margin:2px 0 0; color:var(--muted); font-size:14px; }
.items li:has(.thumb) { grid-template-columns:56px minmax(0,1fr); align-items:start; }
.thumb { width:56px; height:56px; object-fit:contain; background:#fff; border-radius:8px; border:1px solid var(--line); display:block; }
.items li .part { display:block; padding-top:0; }
.items li strong { display:block; line-height:1.4; }
.sub .thumb { width:40px; height:40px; }
.sub .items li:has(.thumb) { grid-template-columns:40px minmax(0,1fr); }
.part, .when { font-size:12px; letter-spacing:.04em; color:var(--muted); padding-top:2px; }
.when { color:var(--accent); font-weight:500; }
.sub .items li p { display:none; }
.sub .items li { padding:6px 0; }
section { display:flex; flex-direction:column; gap:10px; }
.refs ul { margin:0; padding:0; list-style:none; display:flex; flex-wrap:wrap; gap:8px; }
.refs a { display:inline-block; padding:6px 12px; border:1px solid var(--line); border-radius:999px; text-decoration:none; font-size:13px; background:var(--surface); }
.refs a:hover, .refs a:focus-visible { border-color:var(--accent); color:var(--accent); }
.strip { display:grid; grid-template-columns:repeat(auto-fill,minmax(120px,1fr)); gap:12px; }
.strip a { text-decoration:none; }
.strip img { width:100%; aspect-ratio:1100/1300; object-fit:contain; border-radius:10px; background:#fff; display:block; }
.strip span { display:block; font-size:12px; color:var(--muted); margin-top:6px; line-height:1.4; }
footer { font-size:12px; color:var(--muted); }
@media (max-width:680px) { .outfit, .outfit.sub { grid-template-columns:minmax(0,1fr); } .outfit.main { padding:14px; } .sub figure { max-width:260px; } }
"""


def outfit_block(d, o, idx, prefix):
    rows = ""
    for it in o["items"]:
        c = CLOSET[it["id"]]
        rows += (f'<li><img class="thumb" src="{prefix}items/{c["id"]}.jpg" alt="" loading="lazy"><div>'
                 f'<span class="part">{e(c.get("acloset_cat") or PART[c["cat"]])}</span><strong>{e(c["name"])}</strong>')
        rows += (f'<p>{e(it.get("note"))}</p>' if it.get("note") else "") + "</div></li>"
    badge = '<span class="badge">추천</span>' if o.get("pick") else '<span class="badge alt">대안</span>'
    main = "main" if idx == 0 else "sub"
    return (f'<article class="outfit {main}"><figure><img src="{prefix}img/{d["date"]}-{idx + 1}.jpg" alt="{e(o["title"])} 코디" loading="lazy"></figure>'
            f'<div class="desc"><div class="otitle">{badge}<h3>{e(o["title"])}</h3></div><p class="why">{e(o["why"])}</p>'
            f'<ul class="items">{rows}</ul></div></article>')


def render(d, history, prefix):
    w = d["weather"]
    outfits = sorted(d["outfits"], key=lambda o: not o.get("pick"))
    blocks = "".join(outfit_block(d, o, i, prefix) for i, o in enumerate(outfits))
    plan = ""
    if d.get("plan"):
        p = d["plan"]
        opts = "".join(f'<li><span class="when">{e(x["when"])}</span><div><strong>{e(x["name"])}</strong><p>{e(x["desc"])}</p></div></li>' for x in p["options"])
        plan = f'<section><h2>{e(p["title"])}</h2>' + (f'<p class="note">{e(p.get("note"))}</p>' if p.get("note") else "") + f'<ul class="items">{opts}</ul></section>'
    refs = ""
    if d.get("refs"):
        refs = '<section class="refs"><h2>참고한 스타일</h2><ul>' + "".join(
            f'<li><a href="{e(r["url"])}" target="_blank" rel="noopener">{e(r["label"])}</a></li>' for r in d["refs"]) + "</ul></section>"
    hist = ""
    if history:
        hist = '<section><h2>지난 코디</h2><div class="strip">' + "".join(
            f'<a href="{prefix}archive/{h["date"]}.html"><img src="{prefix}img/{h["date"]}-1.jpg" alt="" loading="lazy">'
            f'<span>{e(fmt_date(h["date"], h["weekday"]))}<br>{e(next((o for o in h["outfits"] if o.get("pick")), h["outfits"][0])["title"])}</span></a>'
            for h in history) + "</div></section>"
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>내일의 코디</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;700&family=IBM+Plex+Mono:wght@500&display=swap">
<style>{CSS}</style></head><body><div class="wrap">
<header><span class="eyebrow">ACLOSET 옷장 기반 · 매일 밤 10시 업데이트</span><h1>{e(fmt_date(d['date'], d['weekday']))} 코디</h1></header>
<div class="ribbon"><span class="chip">{e(w['place'])} · {e(w['summary'])}</span><span class="chip">기온 <b>{w['low']}° / {w['high']}°</b></span>
<span class="chip rain">강수확률 <b>{w['rain']}%</b></span><span class="chip tpo">{e(d['tpo']['label'])}</span></div>
<p class="note">{e(w.get('note'))} {e(d['tpo'].get('source'))}</p>
{blocks}{plan}{refs}{hist}
<footer>사진은 Acloset에 등록한 내 옷이에요.</footer></div></body></html>"""


def build():
    days = load_days()
    if not days:
        raise SystemExit("no days")
    (DOCS / "archive").mkdir(parents=True, exist_ok=True)
    for d in days[:30]:
        outfits = sorted(d["outfits"], key=lambda o: not o.get("pick"))
        for i, o in enumerate(outfits):
            p = DOCS / "img" / f"{d['date']}-{i + 1}.jpg"
            if not p.exists() or d is days[0]:
                compose([it["id"] for it in o["items"]], p)
    (DOCS / "items").mkdir(parents=True, exist_ok=True)
    for d in days[:30]:
        for o in d["outfits"]:
            for it in o["items"]:
                src, dst = ITEMS / f"{it['id']}.jpg", DOCS / "items" / f"{it['id']}.jpg"
                if not dst.exists():
                    dst.write_bytes(src.read_bytes())
    for i, d in enumerate(days[:30]):
        (DOCS / "archive" / f"{d['date']}.html").write_text(render(d, [], "../"), encoding="utf-8")
    (DOCS / "index.html").write_text(render(days[0], days[1:13], ""), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("")
    print("built", days[0]["date"])


if __name__ == "__main__":
    build()
