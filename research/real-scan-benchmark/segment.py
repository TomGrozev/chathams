"""Segment ink in ledger-sheet boxes and report blob statistics."""
import json
import sys

import cv2
import numpy as np

CELLS = json.load(open("/tmp/bench/work/cells.json"))
IMG = cv2.imread("/tmp/bench/work/page300.png", cv2.IMREAD_GRAYSCALE)

# ground truth, transcribed by eye from the crops (see findings)
GT = {
    "price": {(1, 1): "1.5", (1, 2): "2.50", (1, 3): "10.50",
              (3, 1): "7.5", (3, 4): "11",
              (4, 1): "6.0", (4, 2): "9"},
    "cash": {(1, 1): "20"},
    "sid": {(3, 1): "A", (3, 2): "C", (3, 3): "D", (3, 4): "F", (3, 5): "2", (3, 6): "V", (3, 7): "1",
            (4, 1): "4", (4, 2): "6", (4, 3): "9", (4, 4): "2", (4, 5): "A", (4, 6): "A", (4, 7): "4"},
}

SPECKS = ["price:6:3", "price:6:9"]


def otsu(img):
    t, _ = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return t


def segment(roi, min_area=20):
    t = otsu(roi)
    ink = (roi < t).astype(np.uint8) * 255
    n, labels, stats, cents = cv2.connectedComponentsWithStats(ink, connectivity=8)
    blobs = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < min_area:
            continue
        mask = (labels[y:y + h, x:x + w] == i).astype(np.uint8)
        blobs.append({"x": int(x + roi_x), "y": int(y + roi_y), "w": int(w), "h": int(h),
                      "area": int(area), "mask": mask})
    blobs.sort(key=lambda b: b["x"])
    return t, blobs


rows_price = []
rows_cash = []
rows_sid = []
for kind, table in (("price", rows_price), ("cash", rows_cash), ("sid", rows_sid)):
    for c in CELLS[kind]:
        key = (c["row"], c["col"])
        if key not in GT[kind]:
            continue
        roi_x, roi_y, w, h = c["roi"]
        roi = IMG[roi_y:roi_y + h, roi_x:roi_x + w]
        t, blobs = segment(roi)
        gt = GT[kind][key]
        expected = len(gt)  # '.' counts as one glyph
        table.append({
            "row": key[0], "col": key[1], "gt": gt, "otsu": float(t),
            "blobs": len(blobs),
            "areas": [b["area"] for b in blobs],
            "boxes": [(b["x"] - roi_x, b["y"] - roi_y, b["w"], b["h"]) for b in blobs],
        })
        print(kind, key, "gt", gt, "expected", expected, "blobs", len(blobs),
              "areas", [b["area"] for b in blobs], "otsu", t)

json.dump({"price": rows_price, "cash": rows_cash, "sid": rows_sid},
          open("/tmp/bench/work/seg_report.json", "w"), indent=1)
