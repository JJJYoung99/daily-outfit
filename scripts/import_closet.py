#!/usr/bin/env python3
"""Import closet items from Acloset grid captures (run on the Mac only).

Each TSV row: <capture-suffix> \t name|sub|color|x|warmth_or_rain|formal (x3 per row, one per grid column)
Captures are 3-column row screenshots; each column is cropped to its garment and saved to closet/items/.
Usage: python3 scripts/import_closet.py <captures_dir> <export_dir>
"""
import json, pathlib, sys
from PIL import Image, ImageChops

ROOT = pathlib.Path(__file__).resolve().parent.parent
ITEMS = ROOT / "closet" / "items"
CATS = {"tops": "top", "bottoms": "bottom", "outers": "outer", "shoes": "shoes", "acc": "acc"}


def find_capture(cap_dir, suffix):
    hits = list(cap_dir.glob(f"*-{suffix}.jpg"))
    if not hits:
        raise SystemExit(f"capture not found: {suffix}")
    return hits[0]


def crop_item(img):
    w, h = img.size
    region = img.crop((0, 0, w, int(h * 0.9)))
    gray = region.convert("L").point(lambda v: 255 if v < 238 else 0)
    box = gray.getbbox()
    if not box:
        return region
    x0, y0, x1, y1 = box
    pad = int(max(x1 - x0, y1 - y0) * 0.04)
    return region.crop((max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(region.height, y1 + pad)))


def main(cap_dir, export_dir):
    cap_dir, export_dir = pathlib.Path(cap_dir), pathlib.Path(export_dir)
    ITEMS.mkdir(parents=True, exist_ok=True)
    closet = []
    for fname, cat in CATS.items():
        n = 0
        for line in (export_dir / f"{fname}.tsv").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            suffix, *cols = line.split("\t")
            img = Image.open(find_capture(cap_dir, suffix)).convert("RGB")
            cw = img.width / 3
            for i, col in enumerate(cols):
                parts = col.split("|")
                if len(parts) == 5:  # shoes/acc: name|sub|color|rain_ok|formal
                    parts.insert(3, "")
                name, sub, color, x, w_or_rain, formal = parts
                if cat in ("shoes", "acc"):
                    x = w_or_rain
                n += 1
                item_id = f"{cat}-{n:03d}"
                tile = img.crop((int(i * cw) + 4, 0, int((i + 1) * cw) - 4, img.height))
                piece = crop_item(tile)
                piece.thumbnail((640, 640), Image.LANCZOS)
                piece.save(ITEMS / f"{item_id}.jpg", quality=86, optimize=True)
                rec = {"id": item_id, "cat": cat, "name": name, "sub": sub, "color": color, "formal": int(formal)}
                if cat in ("shoes", "acc"):
                    rec["rain_ok"] = x == "1"
                else:
                    rec["sleeve"] = x
                    rec["warmth"] = int(w_or_rain)
                closet.append(rec)
    out = ROOT / "closet" / "closet.json"
    out.write_text(json.dumps(closet, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(closet), "items ->", out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
