#!/usr/bin/env python3
"""Build the outfit pages from days/<YYYY-MM-DD>/day.json.

day.json outfits list item ids from closet/closet.json; this script composes each outfit
image from closet/items/<id>.jpg and writes docs/index.html + docs/archive/<date>.html.
"""
import html, json, pathlib, sys
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fallback_pick import pick as rule_pick  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DAYS, DOCS = ROOT / "days", ROOT / "docs"
ITEMS = ROOT / "closet" / "items"
CLOSET = {c["id"]: c for c in json.loads((ROOT / "closet" / "closet.json").read_text(encoding="utf-8"))}
PART = {"top": "상의", "bottom": "하의", "outer": "아우터", "shoes": "신발", "acc": "가방·액세서리"}
W, H = 1100, 1300
TOTAL = 6  # 추천 + 대안 + 옷장 자동 조합을 합쳐 "다른 코디" 버튼으로 넘겨볼 개수
WEEK = "월화수목금토일"


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


def all_outfits(d):
    """Claude가 고른 코디(추천 먼저) 뒤에 같은 날씨·격식 기준의 자동 조합을 붙여 TOTAL개로 채운다."""
    outs = sorted(d["outfits"], key=lambda o: not o.get("pick"))
    if d.get("no_auto"):  # 여행처럼 챙긴 옷만 써야 하는 날은 자동 조합을 붙이지 않는다
        return outs
    pick_items = [CLOSET[it["id"]] for it in outs[0]["items"] if CLOSET[it["id"]]["cat"] != "acc"]
    formal = round(sum(i["formal"] for i in pick_items) / len(pick_items))
    seen = {frozenset(it["id"] for it in o["items"]) for o in outs}
    avoid = {it["id"] for o in outs for it in o["items"] if CLOSET[it["id"]]["cat"] in ("top", "outer")}
    wd = WEEK.index(d["weekday"]) if d.get("weekday") in WEEK else 0
    seed = int(d["date"].replace("-", ""))
    tries = 0
    while len(outs) < TOTAL and tries < 30:
        tries += 1
        try:
            combo = rule_pick(d["weather"], wd, seed * 100 + tries, formal=formal, avoid=avoid)
        except (IndexError, ValueError):
            break
        key = frozenset(i["id"] for i in combo)
        if key in seen:
            continue
        seen.add(key)
        avoid |= {i["id"] for i in combo if i["cat"] in ("top", "outer")}
        main = [i for i in combo if i["cat"] in ("top", "outer")][:2]
        outs.append({"pick": False, "auto": True, "title": " + ".join(i["name"] for i in main),
                     "why": "같은 날씨와 격식 기준(무채색 위주, 포인트 컬러는 하나까지)으로 옷장에서 자동으로 고른 조합이에요.",
                     "items": [{"id": i["id"], "note": ""} for i in combo]})
    return outs


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
.navlink { display:inline-flex; align-items:center; gap:6px; padding:10px 16px; border-radius:999px; background:var(--surface); border:1px solid var(--line); text-decoration:none; font-weight:500; width:fit-content; }
.navlink:hover, .navlink:focus-visible { border-color:var(--accent); color:var(--accent); }
.switch { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.switch button { font:inherit; font-size:15px; font-weight:700; padding:12px 20px; border-radius:999px; border:0; background:var(--fg); color:var(--bg); cursor:pointer; min-height:44px; }
.switch button.ghost { background:transparent; color:var(--fg); border:1px solid var(--line); font-weight:500; padding:12px 16px; }
.switch button:disabled { opacity:.35; cursor:default; }
.switch button:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.switch .count { font-family:var(--mono); font-size:13px; color:var(--muted); font-variant-numeric:tabular-nums; }
.save { font:inherit; font-size:14px; font-weight:500; padding:10px 16px; min-height:44px; border-radius:999px; border:1px solid var(--line); background:var(--surface); color:var(--fg); cursor:pointer; margin-top:12px; }
.save:hover, .save:focus-visible { border-color:var(--accent); color:var(--accent); }
.save[aria-pressed="true"] { background:var(--accent-soft); border-color:var(--accent); color:var(--accent); }
.js .outfit[hidden] { display:none; }
.badge.auto { background:transparent; color:var(--accent); border:1px solid var(--accent); }
footer { font-size:12px; color:var(--muted); }
@media (max-width:680px) { .outfit, .outfit.sub { grid-template-columns:minmax(0,1fr); } .outfit.main { padding:14px; } .sub figure { max-width:260px; } }
"""

JS = """
(function(){
  var cards=[].slice.call(document.querySelectorAll('#outfits .outfit')), n=cards.length, i=0;
  var next=document.getElementById('next'), prev=document.getElementById('prev'), count=document.getElementById('count');
  document.documentElement.classList.add('js');
  if(n<2){ next.hidden=true; prev.hidden=true; count.hidden=true; return; }
  function show(k){
    i=(k+n)%n;
    cards.forEach(function(c,j){ c.hidden = j!==i; });
    count.textContent=(i+1)+' / '+n; prev.disabled = i===0;
  }
  next.addEventListener('click', function(){ show(i+1); cards[i].scrollIntoView({block:'nearest', behavior:'smooth'}); });
  prev.addEventListener('click', function(){ if(i>0){ show(i-1); cards[i].scrollIntoView({block:'nearest', behavior:'smooth'}); } });
})();
"""

SAVE_JS = r"""
(function(){
  var KEY='savedOutfits';
  function load(){ try{ return JSON.parse(localStorage.getItem(KEY))||[]; }catch(e){ return []; } }
  function store(a){ try{ localStorage.setItem(KEY, JSON.stringify(a)); return true; }catch(e){ return false; } }
  function paint(b,on){ b.setAttribute('aria-pressed', on?'true':'false'); b.textContent = on?'저장됨 · 누르면 취소':'이 코디 저장'; }
  [].forEach.call(document.querySelectorAll('button.save'), function(b){
    var v=JSON.parse(b.getAttribute('data-fav'));
    paint(b, load().some(function(x){ return x.id===v.id; }));
    b.addEventListener('click', function(){
      var a=load(), on=a.some(function(x){ return x.id===v.id; });
      if(on){ a=a.filter(function(x){ return x.id!==v.id; }); } else { v.saved=Date.now(); a.push(v); }
      if(store(a)) paint(b,!on); else b.textContent='이 브라우저에서는 저장할 수 없어요';
    });
  });
})();
"""


def outfit_block(d, o, idx, prefix):
    rows = ""
    for it in o["items"]:
        c = CLOSET[it["id"]]
        rows += (f'<li><img class="thumb" src="{prefix}items/{c["id"]}.jpg" alt="" loading="lazy"><div>'
                 f'<span class="part">{e(c.get("acloset_cat") or PART[c["cat"]])}</span><strong>{e(c["name"])}</strong>')
        rows += (f'<p>{e(it.get("note"))}</p>' if it.get("note") else "") + "</div></li>"
    badge = ('<span class="badge">추천</span>' if o.get("pick") else
             '<span class="badge auto">옷장 자동 조합</span>' if o.get("auto") else '<span class="badge alt">대안</span>')
    hidden = " hidden" if idx else ""
    fav = json.dumps({"id": f'{d["date"]}-{idx + 1}', "when": fmt_date(d["date"], d["weekday"]), "title": o["title"], "why": o["why"],
                      "img": f'img/{d["date"]}-{idx + 1}.jpg',
                      "items": [{"id": it["id"], "name": CLOSET[it["id"]]["name"],
                                 "part": CLOSET[it["id"]].get("acloset_cat") or PART[CLOSET[it["id"]]["cat"]]} for it in o["items"]]},
                     ensure_ascii=False)
    return (f'<article class="outfit main" data-i="{idx}"{hidden}><figure><img src="{prefix}img/{d["date"]}-{idx + 1}.jpg" alt="{e(o["title"])} 코디" loading="lazy"></figure>'
            f'<div class="desc"><div class="otitle">{badge}<h3>{e(o["title"])}</h3></div><p class="why">{e(o["why"])}</p>'
            f'<ul class="items">{rows}</ul><button type="button" class="save" data-fav="{e(fav)}">이 코디 저장</button></div></article>')


def render(d, history, prefix):
    w = d["weather"]
    outfits = all_outfits(d)
    blocks = "".join(outfit_block(d, o, i, prefix) for i, o in enumerate(outfits))
    switch = (f'<div class="switch"><button type="button" class="ghost" id="prev" disabled>이전 코디</button>'
              f'<button type="button" id="next">다른 코디 추천</button>'
              f'<span class="count" id="count">1 / {len(outfits)}</span></div>')
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
<header><span class="eyebrow">ACLOSET 옷장 기반 · 매일 저녁 8시 업데이트</span><h1>{e(fmt_date(d['date'], d['weekday']))} 코디</h1></header>
<a class="navlink" href="{prefix}style.html">내 스타일 리포트 · 트렌드 · 쇼핑 리스트 →</a>
<a class="navlink" href="{prefix}favorites.html">저장한 코디 →</a>
<div class="ribbon"><span class="chip">{e(w['place'])} · {e(w['summary'])}</span><span class="chip">기온 <b>{w['low']}° / {w['high']}°</b></span>
<span class="chip rain">강수확률 <b>{w['rain']}%</b></span><span class="chip tpo">{e(d['tpo']['label'])}</span></div>
<p class="note">{e(w.get('note'))} {e(d['tpo'].get('source'))}</p>
{switch}<div id="outfits">{blocks}</div>{refs}{hist}
<footer>사진은 Acloset에 등록한 내 옷이에요.</footer></div>
<script>{JS}</script><script>{SAVE_JS}</script></body></html>"""


NEUTRAL = {"black", "white", "gray", "lightgray", "charcoal", "ivory", "silver"}
COLOR_KO = {"black": "블랙", "white": "화이트", "charcoal": "차콜", "gray": "그레이", "lightgray": "라이트그레이", "ivory": "아이보리",
            "navy": "네이비", "brown": "브라운", "beige": "베이지", "lightblue": "라이트블루", "blue": "블루", "silver": "실버"}
STYLE_CSS = """
.bars { display:flex; flex-direction:column; gap:8px; }
.bar { display:grid; grid-template-columns:92px minmax(0,1fr) 44px; gap:10px; align-items:center; font-size:13px; }
.bar .track { height:12px; background:var(--line); border-radius:999px; overflow:hidden; }
.bar .fill { height:100%; background:var(--fg); border-radius:999px; }
.bar .fill.accent { background:var(--accent); }
.bar b { font-family:var(--mono); font-weight:500; text-align:right; font-variant-numeric:tabular-nums; }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; }
.stat { background:var(--surface); border:1px solid var(--line); border-radius:14px; padding:14px; }
.stat b { display:block; font-family:var(--mono); font-size:26px; font-weight:500; font-variant-numeric:tabular-nums; }
.stat span { font-size:13px; color:var(--muted); }
.card { background:var(--surface); border:1px solid var(--line); border-radius:16px; padding:18px; display:flex; flex-direction:column; gap:10px; }
.card h3 { font-size:17px; }
.card p { margin:0; }
.grid2 { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:14px; }
.tag { display:inline-block; font-size:12px; padding:2px 10px; border-radius:999px; background:var(--accent-soft); color:var(--accent); font-weight:500; }
.mine { font-size:14px; border-left:3px solid var(--accent); padding-left:10px; color:var(--fg); }
.src { font-size:12px; color:var(--muted); display:flex; flex-wrap:wrap; gap:6px; }
.src a { color:var(--muted); }
.thumbs { display:flex; flex-wrap:wrap; gap:8px; }
.thumbs figure { width:84px; margin:0; }
.thumbs img { width:84px; height:84px; object-fit:contain; background:#fff; border:1px solid var(--line); border-radius:10px; display:block; }
.thumbs figcaption { font-size:11px; color:var(--muted); line-height:1.35; margin-top:4px; }
ul.plain { margin:0; padding-left:18px; display:flex; flex-direction:column; gap:6px; }
.navlink { display:inline-flex; align-items:center; gap:6px; padding:10px 16px; border-radius:999px; background:var(--surface); border:1px solid var(--line); text-decoration:none; font-weight:500; width:fit-content; }
.navlink:hover, .navlink:focus-visible { border-color:var(--accent); color:var(--accent); }
"""


def bar_rows(rows, total, accent=lambda k: False):
    return '<div class="bars">' + "".join(
        f'<div class="bar"><span>{e(k)}</span><div class="track"><div class="fill{" accent" if accent(k) else ""}" style="width:{v / total * 100:.1f}%"></div></div><b>{v}</b></div>'
        for k, v in rows) + "</div>"


def thumb(i, prefix):
    c = CLOSET[i]
    return f'<figure><img src="{prefix}items/{i}.jpg" alt="" loading="lazy"><figcaption>{e(c["name"])}</figcaption></figure>'


def render_style(r):
    import collections
    items = list(CLOSET.values())
    n = len(items)
    neutral = sum(i["color"] in NEUTRAL for i in items)
    black = sum(i["color"] == "black" for i in items)
    cats = collections.Counter(PART[i["cat"]] for i in items).most_common()
    colors = collections.Counter(i["color"] for i in items)
    top_colors = [(COLOR_KO.get(k, k), v) for k, v in colors.most_common(8)]
    other = n - sum(v for _, v in colors.most_common(8))
    if other:
        top_colors.append(("기타 컬러", other))
    neutral_ko = {COLOR_KO[k] for k in NEUTRAL if k in COLOR_KO}
    tops = [i for i in items if i["cat"] == "top"]
    casual = sum(i["formal"] == 1 for i in tops)
    d = r["diagnosis"]
    stats = (f'<div class="stats"><div class="stat"><b>{n}</b><span>Acloset 옷 전체</span></div>'
             f'<div class="stat"><b>{neutral / n * 100:.0f}%</b><span>무채색 비율</span></div>'
             f'<div class="stat"><b>{black / n * 100:.0f}%</b><span>블랙 비율</span></div>'
             f'<div class="stat"><b>{casual}/{len(tops)}</b><span>캐주얼 상의</span></div></div>')
    flav = "".join(f'<div class="card"><span class="tag">{e(f["share"])}</span><h3>{e(f["name"])}</h3><p>{e(f["desc"])}</p></div>' for f in d["flavors"])
    diag = (f'<section><h2>내 옷장 분석</h2>{stats}<div class="grid2"><div class="card"><h3>종류</h3>{bar_rows(cats, n)}</div>'
            f'<div class="card"><h3>색</h3>{bar_rows(top_colors, n, lambda k: k not in neutral_ko)}</div></div></section>'
            f'<section><h2>내 스타일</h2><div class="card"><span class="tag">진단</span><h3>{e(d["label"])}</h3><p>{e(d["summary"])}</p></div>'
            f'<div class="grid2">{flav}</div><div class="grid2"><div class="card"><h3>강점</h3><ul class="plain">'
            + "".join(f"<li>{e(x)}</li>" for x in d["strengths"]) + '</ul></div><div class="card"><h3>아쉬운 점</h3><ul class="plain">'
            + "".join(f"<li>{e(x)}</li>" for x in d["gaps"]) + "</ul></div></div></section>")
    f = r["fit"]
    fit = (f'<section><h2>{e(f["title"])}</h2><p class="note">{e(f["caveat"])}</p><div class="grid2">'
           + "".join(f'<div class="card"><h3>{e(x["h"])}</h3><p>{e(x["p"])}</p></div>' for x in f["points"]) + "</div></section>")
    src = r["sources"]
    trends = ('<section><h2>2026 가을·겨울 트렌드</h2><div class="grid2">' + "".join(
        f'<div class="card"><h3>{e(t["name"])}</h3><p>{e(t["desc"])}</p><p class="mine">내 옷장으로: {e(t["mine"])}</p><div class="src">'
        + " · ".join(f'<a href="{e(src[k]["url"])}" target="_blank" rel="noopener">{e(src[k]["label"])}</a>' for k in t["src"]) + "</div></div>"
        for t in r["trends"]) + "</div></section>")
    looks = ""
    for k, l in enumerate(r["looks"], 1):
        rows = "".join(f'<li><img class="thumb" src="items/{i}.jpg" alt="" loading="lazy"><div><span class="part">{e(CLOSET[i].get("acloset_cat") or PART[CLOSET[i]["cat"]])}</span><strong>{e(CLOSET[i]["name"])}</strong></div></li>' for i in l["items"])
        looks += (f'<article class="outfit main"><figure><img src="img/style-{k}.jpg" alt="{e(l["title"])} 코디" loading="lazy"></figure>'
                  f'<div class="desc"><div class="otitle"><span class="badge">트렌드 코디</span><h3>{e(l["title"])}</h3></div><p class="why">{e(l["why"])}</p><ul class="items">{rows}</ul></div></article>')
    looks = f'<section><h2>내 옷으로 따라 하는 트렌드 코디</h2>{looks}</section>'
    mood = ('<section class="refs"><h2>참고 룩북·무드보드</h2><p class="note">런웨이·핀터레스트 사진은 저작권 때문에 직접 싣지 않고 링크로 모았어요.</p><ul>'
            + "".join(f'<li><a href="{e(m["url"])}" target="_blank" rel="noopener">{e(m["label"])}</a></li>' for m in r["moodboards"]) + "</ul></section>")
    buy = ('<section><h2>있으면 좋은 옷</h2><div class="grid2">' + "".join(
        f'<div class="card"><h3>{e(b["what"])}</h3><p>{e(b["why"])}</p>'
        + ('<div class="src">' + " · ".join(f'<a href="{e(x["url"])}" target="_blank" rel="noopener">{e(x["label"])}</a>' for x in b["brands"]) + "</div>" if b["brands"] else "")
        + "</div>" for b in r["buy"]) + "</div></section>")
    clean = ('<section><h2>정리해도 좋을 옷</h2><p class="note">버리라는 뜻은 아니에요. 지금 취향과 잘 안 맞거나 겹치는 옷이라 코디 추천에서 잘 안 쓰이는 후보예요.</p>'
             + "".join(f'<div class="card"><h3>{e(g["group"])}</h3><p>{e(g["why"])}</p><div class="thumbs">' + "".join(thumb(i, "") for i in g["items"]) + "</div></div>" for g in r["clean"])
             + "</section>")
    refs = ('<section class="refs"><h2>출처</h2><ul>' + "".join(
        f'<li><a href="{e(x["url"])}" target="_blank" rel="noopener">{e(x["label"])}</a></li>' for x in src) + "</ul></section>")
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>내 스타일 리포트</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;700&family=IBM+Plex+Mono:wght@500&display=swap">
<style>{CSS}{STYLE_CSS}</style></head><body><div class="wrap">
<a class="navlink" href="./">← 내일의 코디</a>
<header><span class="eyebrow">ACLOSET 옷장 {n}벌 분석 · {e(r["updated"])} 기준</span><h1>내 스타일 리포트</h1></header>
{diag}{fit}{trends}{looks}{mood}{buy}{clean}{refs}
<footer>트렌드와 추천은 위 출처를 바탕으로 정리했어요. 제품 가격·재고는 각 사이트에서 확인하세요.</footer></div></body></html>"""


def build_style():
    f = ROOT / "style" / "report.json"
    if not f.exists():
        return
    r = json.loads(f.read_text(encoding="utf-8"))
    used = set()
    for k, l in enumerate(r["looks"], 1):
        compose(l["items"], DOCS / "img" / f"style-{k}.jpg")
        used |= set(l["items"])
    for g in r["clean"]:
        used |= set(g["items"])
    for i in used:
        dst = DOCS / "items" / f"{i}.jpg"
        if not dst.exists():
            dst.write_bytes((ITEMS / f"{i}.jpg").read_bytes())
    (DOCS / "style.html").write_text(render_style(r), encoding="utf-8")

FAV_JS = r"""
(function(){
  var KEY='savedOutfits', box=document.getElementById('mine');
  function load(){ try{ return JSON.parse(localStorage.getItem(KEY))||[]; }catch(e){ return []; } }
  function el(t,c,txt){ var n=document.createElement(t); if(c) n.className=c; if(txt!=null) n.textContent=txt; return n; }
  function draw(){
    var a=load().slice().reverse(); box.textContent='';
    if(!a.length){ box.appendChild(el('p','note','코디 화면에서 "이 코디 저장"을 누르면 여기에 모여요.')); return; }
    a.forEach(function(v){
      var art=el('article','outfit main'), fig=el('figure'), img=el('img'); img.src=v.img; img.alt=v.title+' 코디'; img.loading='lazy'; fig.appendChild(img);
      var d=el('div','desc'), t=el('div','otitle'); t.appendChild(el('span','badge','저장')); t.appendChild(el('h3',null,v.title)); d.appendChild(t);
      d.appendChild(el('p','note',v.when)); d.appendChild(el('p','why',v.why));
      var ul=el('ul','items');
      v.items.forEach(function(it){ var li=el('li'), th=el('img','thumb'); th.src='items/'+it.id+'.jpg'; th.alt=''; th.loading='lazy';
        var w=el('div'); w.appendChild(el('span','part',it.part)); w.appendChild(el('strong',null,it.name)); li.appendChild(th); li.appendChild(w); ul.appendChild(li); });
      d.appendChild(ul);
      var b=el('button','save','저장 취소'); b.type='button';
      b.addEventListener('click', function(){ try{ localStorage.setItem(KEY, JSON.stringify(load().filter(function(x){ return x.id!==v.id; }))); }catch(e){} draw(); });
      d.appendChild(b); art.appendChild(fig); art.appendChild(d); box.appendChild(art);
    });
  }
  draw();
})();
"""


def build_favorites():
    f = ROOT / "favorites.json"
    favs = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    (DOCS / "fav").mkdir(parents=True, exist_ok=True)
    (DOCS / "items").mkdir(parents=True, exist_ok=True)
    cards = ""
    for v in reversed(favs):
        img = DOCS / "fav" / f"{v['id']}.jpg"
        if not img.exists():
            compose([it["id"] for it in v["items"]], img)
        rows = ""
        for it in v["items"]:
            c = CLOSET[it["id"]]
            dst = DOCS / "items" / f"{c['id']}.jpg"
            if not dst.exists():
                dst.write_bytes((ITEMS / f"{c['id']}.jpg").read_bytes())
            rows += (f'<li><img class="thumb" src="items/{c["id"]}.jpg" alt="" loading="lazy"><div>'
                     f'<span class="part">{e(c.get("acloset_cat") or PART[c["cat"]])}</span><strong>{e(c["name"])}</strong></div></li>')
        cards += (f'<article class="outfit main"><figure><img src="fav/{v["id"]}.jpg" alt="{e(v["title"])} 코디" loading="lazy"></figure>'
                  f'<div class="desc"><div class="otitle"><span class="badge">저장</span><h3>{e(v["title"])}</h3></div>'
                  f'<p class="note">{e(fmt_date(v["date"], v["weekday"]))} · {e(v.get("weather"))} · {e(v.get("tpo"))}</p>'
                  f'<p class="why">{e(v["why"])}</p><ul class="items">{rows}</ul></div></article>')
    if not cards:
        cards = '<p class="note">아직 저장한 코디가 없어요.</p>'
    (DOCS / "favorites.html").write_text(f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>저장한 코디</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;700&family=IBM+Plex+Mono:wght@500&display=swap">
<style>{CSS}</style></head><body><div class="wrap">
<header><span class="eyebrow">마음에 들어서 저장한 코디</span><h1>저장한 코디</h1></header>
<a class="navlink" href="./">← 내일의 코디</a>
<section><h2>버튼으로 저장한 코디</h2><p class="note">이 기기의 이 브라우저에만 저장돼요.</p><div id="mine"></div></section>
<section><h2>따로 보관한 코디</h2><div id="outfits">{cards}</div></section>
<footer>사진은 Acloset에 등록한 내 옷이에요.</footer></div><script>{FAV_JS}</script></body></html>""", encoding="utf-8")


def build():
    days = load_days()
    if not days:
        raise SystemExit("no days")
    (DOCS / "archive").mkdir(parents=True, exist_ok=True)
    for d in days[:30]:
        for i, o in enumerate(all_outfits(d)):
            p = DOCS / "img" / f"{d['date']}-{i + 1}.jpg"
            if not p.exists() or d is days[0]:
                compose([it["id"] for it in o["items"]], p)
    (DOCS / "items").mkdir(parents=True, exist_ok=True)
    for d in days[:30]:
        for o in all_outfits(d):
            for it in o["items"]:
                src, dst = ITEMS / f"{it['id']}.jpg", DOCS / "items" / f"{it['id']}.jpg"
                if not dst.exists():
                    dst.write_bytes(src.read_bytes())
    for i, d in enumerate(days[:30]):
        (DOCS / "archive" / f"{d['date']}.html").write_text(render(d, [], "../"), encoding="utf-8")
    (DOCS / "index.html").write_text(render(days[0], days[1:13], ""), encoding="utf-8")
    build_style()
    build_favorites()
    (DOCS / ".nojekyll").write_text("")
    print("built", days[0]["date"])


if __name__ == "__main__":
    build()
