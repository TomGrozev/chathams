import cv2
import json
import numpy as np

img = cv2.imread("/tmp/bench/work/page300.png", cv2.IMREAD_GRAYSCALE)
H, W = img.shape
# rules are printed in grey ~150-215; handwriting ink is darker (<120) at its core.
rules = ((img >= 110) & (img <= 235)).astype(np.uint8) * 255
rules = cv2.morphologyEx(rules, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
# keep only long straight runs so stray mid-grey ink edges drop out
hk = cv2.morphologyEx(rules, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1)))
vk = cv2.morphologyEx(rules, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40)))
rules = cv2.bitwise_or(hk, vk)
rules = cv2.morphologyEx(rules, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
cv2.imwrite("/tmp/bench/work/rules.png", rules)
free = (rules == 0).astype(np.uint8) * 255
n, labels, stats, cents = cv2.connectedComponentsWithStats(free, connectivity=4)
print("components", n)
cells = []
sizes = []
for i in range(1, n):
    x, y, w, h, area = stats[i]
    if w > 30 and h > 30 and area > 1000:
        cells.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})
        sizes.append((w, h))
print("cells >30px:", len(cells))
from collections import Counter
print("common sizes:", Counter(sizes).most_common(12))
print("biggest:", sorted(sizes, key=lambda s: -s[0] * s[1])[:3])
json.dump(cells, open("/tmp/bench/work/cells2.json", "w"), indent=0)
