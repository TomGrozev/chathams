"""Render per-box Otsu masks with component boxes drawn, for failure-kind naming."""
import json

import cv2
import numpy as np

CELLS = json.load(open("/tmp/bench/work/cells.json"))
IMG = cv2.imread("/tmp/bench/work/page300.png", cv2.IMREAD_GRAYSCALE)


def otsu(img):
    t, _ = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return t


def blob_mask(roi, min_area=8):
    t = otsu(roi)
    ink = (roi < t).astype(np.uint8) * 255
    n, labels, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    out = np.zeros_like(ink)
    keep = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < min_area:
            continue
        out[labels == i] = 255
        keep.append((x, y, w, h, area))
    keep.sort(key=lambda k: k[0])
    return t, out, keep


targets = [("price", 1, 1), ("price", 1, 2), ("price", 1, 3), ("price", 3, 1),
           ("price", 3, 4), ("price", 4, 1), ("price", 4, 2), ("cash", 1, 1)]
tiles = []
for kind, r, c in targets:
    cell = next(x for x in CELLS[kind] if x["row"] == r and x["col"] == c)
    x0, y0, w, h = cell["roi"]
    roi = IMG[y0:y0 + h, x0:x0 + w]
    t, m, keep = blob_mask(roi)
    vis = cv2.cvtColor(m, cv2.COLOR_GRAY2BGR)
    for i, (x, y, bw, bh, area) in enumerate(keep):
        cv2.rectangle(vis, (x, y), (x + bw, y + bh), (0, 0, 255), 1)
        cv2.putText(vis, str(i), (x, max(10, y - 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 150, 0), 1)
    tiles.append(cv2.resize(vis, None, fx=1.3, fy=1.3, interpolation=cv2.INTER_NEAREST))
    print(kind, r, c, "otsu", t, "blobs", [(x, y, bw, bh, a) for x, y, bw, bh, a in keep])

H = max(t.shape[0] for t in tiles)
W = sum(t.shape[1] for t in tiles) + 8 * (len(tiles) + 1)
canvas = np.full((H + 16, W, 3), 128, np.uint8)
x = 8
for t in tiles:
    canvas[8:8 + t.shape[0], x:x + t.shape[1]] = t
    x += t.shape[1] + 8
cv2.imwrite("/tmp/bench/work/m_blobs.png", canvas)
print("canvas", canvas.shape)
