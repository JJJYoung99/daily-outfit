#!/usr/bin/env python3
"""Give every closet item an Acloset-style name: 브랜드 + 색상 + (디테일) + 카테고리.

Acloset stores no free-text item name, only brand / category / color, so the display
name is built from those. `desc` keeps the longer description used while exporting.
Usage: python3 scripts/name_items.py <export_dir>   (reads brands_<cat>.txt files)
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = {"top": "tops", "bottom": "bottoms", "outer": "outers", "shoes": "shoes", "acc": "acc"}
COLOR = {"black": "블랙", "white": "화이트", "gray": "그레이", "lightgray": "라이트그레이", "charcoal": "차콜", "ivory": "아이보리",
         "cream": "크림", "beige": "베이지", "khaki": "카키", "brown": "브라운", "darkbrown": "다크브라운", "navy": "네이비",
         "blue": "블루", "lightblue": "라이트블루", "skyblue": "스카이블루", "bluegray": "블루그레이", "indigo": "인디고",
         "olive": "올리브", "greengray": "그린그레이", "darkgreen": "다크그린", "red": "레드", "camel": "카멜", "taupe": "토프",
         "silver": "실버", "darkpurple": "다크퍼플"}
DETAIL = ["핀스트라이프", "글렌체크", "헤링본", "깅엄", "노르딕", "스트라이프", "체크", "그래픽", "레터링", "로고", "케이블",
          "모크넥", "터틀넥", "브이넥", "하프집", "헨리넥", "오픈카라", "폴로", "퀼팅", "코듀로이", "스웨이드", "레더", "벨벳",
          "나일론", "워크", "웨스턴", "트러커", "해링턴", "블루종", "라이더", "봄버", "더블", "싱글", "발마칸", "롱", "숏",
          "오버핏", "투턱", "벌룬", "커브드", "와이드", "테이퍼드", "스트레이트", "밴딩", "카펜터", "파라슈트", "치노",
          "트랙", "후드", "풋볼", "럭비", "링거", "캡토", "윙팁", "페니", "첼시", "데저트", "저먼", "러닝", "청키", "캔버스", "니트", "메신저", "호보"]
CAT = {
    "top": {"tee": "반팔 티셔츠", "longsleeve": "긴팔 티", "polo": "카라 티", "tank": "탱크탑", "shirt": "셔츠", "sweat": "맨투맨",
            "hoodie": "후드", "knit": "니트", "cardigan": "가디건"},
    "bottom": {"denim": "청바지", "slacks": "정장바지", "pants": "긴바지", "jogger": "트레이닝 바지", "shorts": "반바지"},
    "outer": {"coat": "코트", "parka": "패딩", "puffer": "패딩", "blazer": "블레이저", "jacket": "재킷", "hoodiezip": "후드 집업",
              "windbreaker": "바람막이", "cardigan": "가디건", "knitzip": "니트 집업", "vest": "베스트"},
    "shoes": {"sneaker": "스니커즈", "sport": "운동화", "loafer": "로퍼", "derby": "구두", "oxford": "구두", "boots": "부츠", "sandal": "슬리퍼"},
    "acc": {"bag": "가방", "jewelry": "주얼리"},
}


def acloset_cat(it, desc):
    if it["cat"] == "acc":
        for k, v in (("메신저", "크로스백"), ("백팩", "백팩"), ("호보", "숄더백"), ("링", "반지"), ("목걸이", "목걸이")):
            if k in desc:
                return v
    if it["cat"] == "bottom" and "카고" in desc:
        return "카고바지"
    if it["cat"] == "outer" and "무스탕" in desc:
        return "무스탕"
    if it["cat"] == "shoes" and "슬립온" in desc:
        return "슬립온"
    c = CAT[it["cat"]].get(it["sub"], it["sub"])
    if it["cat"] == "top" and it.get("sleeve") == "s" and c in ("셔츠", "니트"):
        c = "반팔 " + c
    return c


def main(export_dir):
    export_dir = pathlib.Path(export_dir)
    path = ROOT / "closet" / "closet.json"
    closet = json.loads(path.read_text(encoding="utf-8"))
    brands = {}
    for cat, f in FILES.items():
        seq = [b.strip() for line in (export_dir / f"brands_{f}.txt").read_text(encoding="utf-8").splitlines() for b in line.split("|") if b.strip()]
        items = [i for i in closet if i["cat"] == cat]
        assert len(seq) == len(items), (cat, len(seq), len(items))
        for it, b in zip(items, seq):
            brands[it["id"]] = b
    for it in closet:
        desc = it.get("desc") or it["name"]
        it["desc"] = desc
        it["brand"] = "" if brands[it["id"]] == "No Brand" else brands[it["id"]]
        it["acloset_cat"] = acloset_cat(it, desc)
        cat_word = it["acloset_cat"]
        detail = next((d for d in DETAIL if d in desc and d not in cat_word), "")
        parts = [it["brand"], COLOR.get(it["color"], it["color"]), detail, cat_word]
        it["name"] = " ".join(p for p in parts if p)
    path.write_text(json.dumps(closet, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(closet), "named")


if __name__ == "__main__":
    main(sys.argv[1])
