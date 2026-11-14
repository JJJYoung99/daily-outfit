#!/usr/bin/env python3
"""Backup picker: if Claude's nightly routine did not write tomorrow's day.json,
pick an outfit from the closet by weather + style rules so the page still updates.

Rules (user's taste): modern, achromatic first; at most ONE accent color per outfit.
"""
import datetime as dt, json, pathlib, random, urllib.request
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLOSET = json.loads((ROOT / "closet" / "closet.json").read_text(encoding="utf-8"))
NEUTRAL = {"black", "white", "gray", "lightgray", "charcoal", "ivory", "silver"}
WEEK = "월화수목금토일"
WMO = {0: "맑음", 1: "대체로 맑음", 2: "구름 조금", 3: "흐림", 45: "안개", 48: "안개", 51: "이슬비", 53: "이슬비", 55: "이슬비",
       61: "비", 63: "비", 65: "강한 비", 71: "눈", 73: "눈", 75: "많은 눈", 80: "소나기", 81: "소나기", 82: "강한 소나기", 95: "뇌우"}


def weather(day):
    url = ("https://api.open-meteo.com/v1/forecast?latitude=37.53&longitude=126.98&timezone=Asia%2FSeoul"
           f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code&start_date={day}&end_date={day}")
    with urllib.request.urlopen(url, timeout=20) as r:
        d = json.load(r)["daily"]
    return {"low": round(d["temperature_2m_min"][0]), "high": round(d["temperature_2m_max"][0]),
            "rain": int(d["precipitation_probability_max"][0] or 0), "summary": WMO.get(d["weather_code"][0], "흐림")}


def accents(items):
    return {i["color"] for i in items if i["color"] not in NEUTRAL}


def pick(w, weekday, seed):
    rnd = random.Random(seed)
    avg = (w["low"] + w["high"]) / 2
    rainy = w["rain"] >= 50
    formal = 2 if weekday < 5 else 1
    by = lambda cat, f=lambda i: True: [i for i in CLOSET if i["cat"] == cat and f(i)]
    sleeve = "s" if avg >= 22 else "l"
    tops = by("top", lambda i: i["sleeve"] == sleeve and i["sub"] not in ("tank",) and abs(i["formal"] - formal) <= 1)
    if avg < 15:
        tops = [i for i in tops if i["sub"] in ("knit", "shirt", "sweat", "hoodie", "longsleeve", "polo")]
    bottoms = by("bottom", lambda i: i["sub"] != "shorts" or avg >= 25)
    want_warm = 3 if avg < 8 else 2 if avg < 15 else 1
    outers = by("outer", lambda i: i["warmth"] == want_warm) if avg < 20 else []
    shoes = by("shoes", lambda i: i["sub"] not in ("sport", "sandal") and (i["rain_ok"] or not rainy))
    bags = by("acc", lambda i: i["sub"] == "bag")
    for _ in range(400):
        combo = [rnd.choice(tops), rnd.choice(bottoms), rnd.choice(shoes)]
        if outers:
            combo.insert(1, rnd.choice(outers))
        if len(accents(combo)) <= 1 and max(i["formal"] for i in combo) - min(i["formal"] for i in combo) <= 1:
            return combo + [rnd.choice(bags)]
    return combo + [rnd.choice(bags)]


def main():
    now = dt.datetime.now(ZoneInfo("Asia/Seoul"))
    tmr = (now + dt.timedelta(days=1)).date()
    out = ROOT / "days" / tmr.isoformat() / "day.json"
    if out.exists():
        print("already exists", out)
        return
    w = weather(tmr.isoformat())
    a, b = pick(w, tmr.weekday(), tmr.toordinal()), pick(w, tmr.weekday(), tmr.toordinal() + 7)
    gap = w["high"] - w["low"]
    note = f"최저 {w['low']}°, 최고 {w['high']}°예요." + (" 일교차가 커서 겉옷을 챙기세요." if gap >= 8 else "") + (" 비 소식이 있어 가죽이나 고무 밑창 신발로 골랐어요." if w["rain"] >= 50 else "")
    mk = lambda combo: [{"id": i["id"], "note": ""} for i in combo]
    title = lambda combo: " + ".join(i["name"] for i in combo[:2])
    day = {"date": tmr.isoformat(), "weekday": WEEK[tmr.weekday()],
           "weather": {"place": "서울", **w, "note": note},
           "tpo": {"label": "평일 출근" if tmr.weekday() < 5 else "휴일 외출", "source": "오늘은 자동 백업 추천이에요. 일정은 반영되지 않았어요."},
           "outfits": [{"pick": True, "title": title(a), "why": "무채색 위주에 포인트 컬러는 하나까지만 쓰는 기준으로 날씨에 맞춰 골랐어요.", "items": mk(a)},
                       {"pick": False, "title": title(b), "why": "같은 기준의 다른 조합이에요.", "items": mk(b)}],
           "refs": []}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(day, ensure_ascii=False, indent=1), encoding="utf-8")
    print("fallback written", out)


if __name__ == "__main__":
    main()
