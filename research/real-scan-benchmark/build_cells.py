import cv2
import json
import numpy as np

img = cv2.imread("/tmp/bench/work/page300.png", cv2.IMREAD_GRAYSCALE)
cells = json.load(open("/tmp/bench/work/cells2.json"))

price = [c for c in cells if 145 <= c["w"] <= 172 and 180 <= c["h"] <= 205]
sid = [c for c in cells if 80 <= c["w"] <= 100 and 100 <= c["h"] <= 125]

rows_y = [373, 600, 831, 1061, 1288, 1519, 1749, 1978]
# price columns from a clean row (interiors)
rowref = sorted([c for c in price if abs(c["y"] - 1749) < 40], key=lambda c: c["x"])
price_x = [c["x"] for c in rowref[:12]]
cash_x = [c["x"] for c in rowref[12:]]
cash_y = {}
for c in price:
    if c["x"] > 3000:
        cash_y.setdefault(round(c["y"] / 60), []).append(c)

PW, PH = 157, 193
SW, SH = 89, 111
sid_rows_y = sorted({round(c["y"] / 50) * 50 for c in sid})
# build sid lattice from detection directly (7 cells per row)
sid_x = [55, 162, 269, 376, 483, 590, 698]

out = {"price": [], "cash": [], "sid": []}
for ri, y in enumerate(rows_y, start=1):
    for ci, x in enumerate(price_x, start=1):
        out["price"].append({"row": ri, "col": ci, "x": x, "y": y, "w": PW, "h": PH})
    # cash cells: detected interior near this row
    cand = [c for c in price if c["x"] > 3000 and abs(c["y"] - y) < 45]
    for ci, c in enumerate(sorted(cand, key=lambda c: c["x"]), start=1):
        out["cash"].append({"row": ri, "col": ci, "x": c["x"], "y": c["y"], "w": c["w"], "h": c["h"]})

for ri, y in zip(range(3, 9), [829, 1059, 1287, 1517, 1748, 1976]):
    for ci, x in enumerate(sid_x, start=1):
        out["sid"].append({"row": ri, "col": ci, "x": x, "y": y, "w": SW, "h": SH})

print("price cells", len(out["price"]), "cash", len(out["cash"]), "sid", len(out["sid"]))
for c in out["cash"]:
    print("cash", c)

INSET = 3
for kind in ("price", "cash", "sid"):
    for c in out[kind]:
        x, y, w, h = c["x"] + INSET, c["y"] + INSET, c["w"] - 2 * INSET, c["h"] - 2 * INSET
        roi = img[y:y + h, x:x + w]
        c["roi"] = [int(x), int(y), int(w), int(h)]
        c["ink"] = int((roi < 128).sum())
        c["ink_mid"] = int((roi < 190).sum())

json.dump(out, open("/tmp/bench/work/cells.json", "w"), indent=0)
for kind in ("price", "cash", "sid"):
    ne = [c for c in out[kind] if c["ink"] > 40]
    print(kind, "non-empty (ink>40):", len(ne))
    for c in ne:
        print("  ", kind, "r%s c%s" % (c["row"], c["col"]), "ink", c["ink"], "roi", c["roi"])
