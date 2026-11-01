"""Does the light grey rule survive Otsu thresholding, and at which threshold can
the contour-based cell finder still separate the price boxes?"""
import json

import cv2
import numpy as np

IMG = cv2.imread("/tmp/bench/work/page300.png", cv2.IMREAD_GRAYSCALE)
CELLS = json.load(open("/tmp/bench/work/cells.json"))

# 1. page-level Otsu
otsu_t, _ = cv2.threshold(IMG, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
print("page Otsu threshold:", otsu_t)

# 2. grey level of rule pixels: sample the rule bands that the detection found
xs = sorted({c["x"] for c in CELLS["price"]})
ys = sorted({c["y"] for c in CELLS["price"]})
rule_vals = []
for x in xs[:12]:
    for y in ys[:3]:
        # horizontal rule just above each cell interior
        seg = IMG[max(0, y - 6):y, x + 10:x + 60]
        rule_vals.append(seg.min(axis=0))
        vert = IMG[y + 10:y + 60, max(0, x - 6):x]
        rule_vals.append(vert.min(axis=1))
vals = np.concatenate(rule_vals)
print("rule pixel grey: min %d p1 %d p5 %d median %d p95 %d max %d" % (
    vals.min(), np.percentile(vals, 1), np.percentile(vals, 5), np.median(vals),
    np.percentile(vals, 95), vals.max()))

# 3. how much of the rule survives thresholding at T (fraction of rule pixels below T)
for T in (150, 180, 195, 200, 205, 210, 215, 220, 230, 235, 240, 245):
    frac = float((vals < T).mean())
    ink_frac = float((IMG < T).mean())
    print(f"T={T:3d} rule pixels kept {frac:.3f} page ink fraction {ink_frac:.4f}")

# 4. contour-free cell test: count separated white cell interiors at each threshold
def count_cells(T, dilate=0):
    binary = (IMG < T).astype(np.uint8) * 255
    if dilate:
        binary = cv2.dilate(binary, np.ones((3, 3), np.uint8), iterations=dilate)
    free = (binary == 0).astype(np.uint8) * 255
    n, labels, stats, _ = cv2.connectedComponentsWithStats(free, connectivity=4)
    found = 0
    for i in range(1, n):
        w, h = stats[i][2], stats[i][3]
        if 145 <= w <= 172 and 180 <= h <= 205:
            found += 1
    return found


print("\nprice cells recovered out of 96, no dilation:")
for T in (200, 210, 220, 230, 235, 240, 245, 250):
    print(f"  T={T}: {count_cells(T)}")
print("price cells recovered with the table_reader dilate(5) step:")
for T in (int(otsu_t), 235, 240):
    print(f"  T={T}: {count_cells(T, dilate=5)}")
