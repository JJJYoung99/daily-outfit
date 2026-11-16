#!/usr/bin/env python3
"""옷장 로테이션 도우미.
usage.py [YYYY-MM-DD] [평균기온]  -> 그 날짜 이전 days/ 기록을 보고, 아직 한 번도 추천 안 된 옷과
가장 오래 안 나온 옷을 카테고리별로 보여준다(exclude 옷 제외). 루틴이 옷을 고를 때 참고한다."""
import json, pathlib, sys, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLOSET = json.loads((ROOT / "closet" / "closet.json").read_text(encoding="utf-8"))
BRANDS = json.loads((ROOT / "closet" / "brands.json").read_text(encoding="utf-8"))
TIER = {b: t for t in ("premium", "designer", "core") for b in BRANDS[t]}


def tier(item):
    return TIER.get(item.get("brand", ""), "basic")


def fits_weather(i, avg):
    """날씨에 안 맞는 옷(겨울 반팔·여름 바지·한여름 패딩 등)은 로테이션 후보에서 뺀다."""
    if i["cat"] == "top" and i.get("sleeve") == "s" and avg < 22:
        return False
    if i["cat"] == "top" and i.get("sleeve") == "l" and avg >= 25:
        return False
    if i.get("season") == "summer" and avg < 20:
        return False
    if i["cat"] == "bottom" and i.get("sub") == "shorts" and avg < 25:
        return False
    if i["cat"] == "outer" and avg >= 20:
        return False
    return True


def history(before=None):
    """id -> (횟수, 마지막 날짜). 추천(pick)은 2점, 대안은 1점."""
    cnt, last = collections.Counter(), {}
    for f in sorted((ROOT / "days").glob("*/day.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if before and d["date"] >= before:
            continue
        for o in d.get("outfits", []):
            for it in o["items"]:
                cnt[it["id"]] += 2 if o.get("pick") else 1
                last[it["id"]] = d["date"]
    return cnt, last


def main():
    before = sys.argv[1] if len(sys.argv) > 1 else None
    avg = float(sys.argv[2]) if len(sys.argv) > 2 else None
    cnt, last = history(before)
    by = collections.defaultdict(list)
    for i in CLOSET:
        if i.get("exclude"):
            continue
        if avg is not None and not fits_weather(i, avg):
            continue
        by[i["cat"]].append(i)
    for cat in ("top", "outer", "bottom", "shoes", "acc"):
        items = sorted(by[cat], key=lambda i: (cnt[i["id"]], last.get(i["id"], ""), tier(i) == "basic"))
        never = [i for i in items if cnt[i["id"]] == 0]
        print(f"## {cat}: 미추천 {len(never)}/{len(items)}")
        for i in items[:25]:
            print(f"  {i['id']} [{tier(i)}] {i['name']} (f{i['formal']} w{i.get('warmth','-')}{' summer' if i.get('season') else ''}) "
                  f"횟수 {cnt[i['id']]} 마지막 {last.get(i['id'], '-')}")


if __name__ == "__main__":
    main()
