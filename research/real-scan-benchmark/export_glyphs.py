import json
import os

import cv2
import numpy as np

CELLS = json.load(open("/tmp/bench/work/cells.json"))
IMG = cv2.imread("/tmp/bench/work/page300.png", cv2.IMREAD_GRAYSCALE)
OUT = "/tmp/bench/work/glyphs"
os.makedirs(OUT, exist_ok=True)

GT = {"price": {(1, 1), (1, 2), (1, 3), (3, 1), (3, 4), (4, 1), (4, 2)},
      "cash": {(1, 1)},
      "sid": {(3, i) for i in range(1, 8)} | {(4, i) for i in range(1, 8)}}

manifest = []
for kind, keys in GT.items():
    for cell in CELLS[kind]:
        key = (cell["row"], cell["col"])
        if key not in keys:
            continue
        x0, y0, w, h = cell["roi"]
        roi = IMG[y0:y0 + h, x0:x0 + w]
        _, t = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        n, labels, stats, _ = cv2.connectedComponentsWithStats(t, connectivity=8)
        blobs = []
        H, W = roi.shape
        for i in range(1, n):
            x, y, bw, bh, area = stats[i]
            if area < 8 or x <= 0 or y <= 0 or x + bw >= W or y + bh >= H:
                continue
            blobs.append((x, y, bw, bh, i))
        blobs.sort(key=lambda b: b[0])
        for gi, (x, y, bw, bh, i) in enumerate(blobs):
            mask = (labels == i).astype(np.uint8)
            glyph = np.where(mask[y:y + bh, x:x + bw] > 0, 0, 255).astype(np.uint8)
            pad = 8
            canvas = cv2.copyMakeBorder(glyph, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)
            canvas = cv2.resize(canvas, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
            path = f"{OUT}/{kind}_{key[0]}_{key[1]}_{gi}.png"
            cv2.imwrite(path, canvas)
            manifest.append({"kind": kind, "row": key[0], "col": key[1], "idx": gi, "path": path,
                             "area": int(area), "h": int(bh), "w": int(bw)})

json.dump(manifest, open("/tmp/bench/work/glyphs.json", "w"), indent=1)
print("glyphs", len(manifest))
