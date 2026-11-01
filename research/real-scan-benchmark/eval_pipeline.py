"""Run the full CPU recognizer path on the scan, score it against the transcribed
ground truth, and time each stage."""
import json
import os
import time

import cv2
import numpy as np
import torch
import torch.nn.functional as F

CELLS = json.load(open("/tmp/bench/work/cells.json"))
SCAN = "/home/dev/workspace/test_scan.pdf"
MODEL_DIR = "/tmp/bench/work/models"

GT_PRICE = {(1, 1): "1.5", (1, 2): "2.50", (1, 3): "10.50",
            (3, 1): "7.5", (3, 4): "11", (4, 1): "6.0", (4, 2): "9"}
GT_CASH = {(1, 1): "20"}
GT_SID = {(3, 1): "A", (3, 2): "C", (3, 3): "D", (3, 4): "F", (3, 5): "2", (3, 6): "V", (3, 7): "1",
          (4, 1): "4", (4, 2): "6", (4, 3): "9", (4, 4): "2", (4, 5): "A", (4, 6): "A", (4, 7): "4"}

CLASSES36 = [str(i) for i in range(10)] + [chr(ord("A") + i) for i in range(26)]


def load_model(name, n_classes):
    import torch.nn as nn

    class CNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.c1 = nn.Conv2d(1, 32, 3, padding=1)
            self.c2 = nn.Conv2d(32, 64, 3, padding=1)
            self.fc1 = nn.Linear(64 * 7 * 7, 128)
            self.fc2 = nn.Linear(128, n_classes)

        def forward(self, x):
            x = F.max_pool2d(F.relu(self.c1(x)), 2)
            x = F.max_pool2d(F.relu(self.c2(x)), 2)
            x = x.flatten(1)
            x = F.relu(self.fc1(x))
            return self.fc2(x)

    m = CNN()
    m.load_state_dict(torch.load(f"{MODEL_DIR}/{name}.pt", map_location="cpu"))
    m.eval()
    return m


def emnist_normalise(mask):
    """mask: uint8 ink mask (255 = ink). Return 28x28 float tensor, EMNIST style."""
    ys, xs = np.nonzero(mask)
    crop = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = crop.shape
    scale = 20.0 / max(h, w)
    nh, nw = max(1, int(round(h * scale))), max(1, int(round(w * scale)))
    small = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)
    tile = np.zeros((28, 28), np.float32)
    oy, ox = (28 - nh) // 2, (28 - nw) // 2
    tile[oy:oy + nh, ox:ox + nw] = small.astype(np.float32) / 255.0
    return torch.from_numpy(tile).unsqueeze(0).unsqueeze(0)


def blobs_from_roi(roi, min_area=8, drop_border=True):
    _, t = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(t, connectivity=8)
    out = []
    H, W = roi.shape
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < min_area:
            continue
        if drop_border and (x <= 0 or y <= 0 or x + w >= W or y + h >= H):
            continue  # rule fragment that spilled into the cut-out
        out.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h),
                    "area": int(area), "mask": (labels == i).astype(np.uint8) * 255})
    out.sort(key=lambda b: b["x"])
    return t, out


def classify(model, mask, classes):
    x = emnist_normalise(mask)
    with torch.no_grad():
        probs = F.softmax(model(x), dim=1)[0]
    p, idx = torch.max(probs, 0)
    return classes[int(idx)], float(p), probs


def rasterise(path, dpi=300):
    import pymupdf

    doc = pymupdf.open(path)
    page = doc[0]
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    return arr.copy()


def main():
    digits = load_model("digits", 10)
    alnum = load_model("alnum", 36) if os.path.exists(f"{MODEL_DIR}/alnum.pt") else None
    print("alnum model present:", alnum is not None)

    t_raster = time.perf_counter()
    img = rasterise(SCAN)
    raster_ms = (time.perf_counter() - t_raster) * 1000

    stage = {"cut": 0.0, "seg": 0.0, "infer": 0.0}
    results = {"price": [], "cash": [], "sid": []}

    def handle(kind, gt_table, model, classes):
        for cell in CELLS[kind]:
            key = (cell["row"], cell["col"])
            if key not in gt_table:
                continue
            t0 = time.perf_counter()
            x0, y0, w, h = cell["roi"]
            roi = img[y0:y0 + h, x0:x0 + w].copy()
            stage["cut"] += time.perf_counter() - t0
            t0 = time.perf_counter()
            _, blobs = blobs_from_roi(roi)
            stage["seg"] += time.perf_counter() - t0
            t0 = time.perf_counter()
            glyphs = []
            for b in blobs:
                ch, p, _ = classify(model, b["mask"], classes)
                glyphs.append({"char": ch, "p": p, "h": b["h"], "w": b["w"],
                               "area": b["area"], "x": b["x"]})
            stage["infer"] += time.perf_counter() - t0
            results[kind].append({"row": key[0], "col": key[1], "gt": gt_table[key],
                                  "glyphs": glyphs})

    handle("price", GT_PRICE, digits, [str(i) for i in range(10)])
    handle("cash", GT_CASH, digits, [str(i) for i in range(10)])
    if alnum is not None:
        handle("sid", GT_SID, alnum, CLASSES36)

    # compose amounts: a glyph is a '.' when it is short and low and small-area
    def compose(glyphs):
        if not glyphs:
            return "", None
        heights = [g["h"] for g in glyphs]
        maxh = max(heights)
        out = ""
        minp = 1.0
        for g in glyphs:
            if g["h"] <= 0.35 * maxh and g["w"] <= 0.35 * maxh and g["area"] < 70:
                out += "."
            else:
                out += g["char"]
            minp = min(minp, g["p"])
        return out, minp

    print("\n--- amount boxes (CNN digits, zero-shot) ---")
    exact = 0
    total = 0
    chars_right = chars_total = 0
    for r in results["price"] + results["cash"]:
        pred, minp = compose(r["glyphs"])
        ok = pred == r["gt"]
        exact += ok
        total += 1
        chars_total += len(r["gt"])
        chars_right += sum(1 for a, b in zip(pred, r["gt"]) if a == b) if len(pred) == len(r["gt"]) else 0
        print(f"{r['row']},{r['col']} gt={r['gt']:6s} pred={pred:8s} exact={ok} "
              f"minp={minp if minp is None else round(minp, 3)} "
              f"blobs={[(g['char'], round(g['p'], 3), g['area']) for g in r['glyphs']]}")
    print(f"amount boxes exact {exact}/{total} chars {chars_right}/{chars_total}")

    if results["sid"]:
        print("\n--- sid cells (CNN alnum, zero-shot) ---")
        s_exact = s_total = 0
        sid_confs = []
        for r in results["sid"]:
            if not r["glyphs"]:
                print(f"{r['row']},{r['col']} gt={r['gt']} pred=None")
                s_total += 1
                continue
            g = r["glyphs"][0]
            ok = g["char"] == r["gt"]
            s_exact += ok
            s_total += 1
            sid_confs.append((r["row"], r["col"], r["gt"], g["char"], round(g["p"], 3)))
            print(f"{r['row']},{r['col']} gt={r['gt']} pred={g['char']} p={g['p']:.3f} ok={ok}")
        print(f"sid cells exact {s_exact}/{s_total}")

    # flag rates: minimum glyph confidence per box
    print("\n--- flag rates at threshold T (box flagged when min glyph prob < T) ---")
    boxes = []
    for r in results["price"] + results["cash"]:
        _, minp = compose(r["glyphs"])
        boxes.append(minp if minp is not None else 0.0)
    for r in results["sid"]:
        boxes.append(min(r["glyphs"][0]["p"] for r in [r]) if r["glyphs"] else 0.0)
    for T in (0.5, 0.7, 0.9, 0.95, 0.99, 0.999):
        n = sum(1 for b in boxes if b < T)
        print(f"T={T}: flagged {n}/{len(boxes)} ({100 * n / len(boxes):.0f}%)")

    # full page: every one of the 154 cells through cut, segment, inference
    t0 = time.perf_counter()
    n_blobs = 0
    for kind in ("price", "cash", "sid"):
        model = alnum if (kind == "sid" and alnum is not None) else digits
        classes = CLASSES36 if (kind == "sid" and alnum is not None) else [str(i) for i in range(10)]
        for cell in CELLS[kind]:
            x0, y0, w, h = cell["roi"]
            roi = img[y0:y0 + h, x0:x0 + w].copy()
            _, blobs = blobs_from_roi(roi)
            for b in blobs:
                classify(model, b["mask"], classes)
                n_blobs += 1
    full_ms = (time.perf_counter() - t0) * 1000
    print(f"full page (154 cells, {n_blobs} blobs): {full_ms:.0f} ms")

    infer_ms = sum(stage.values()) * 1000
    print(f"\ntiming: raster {raster_ms:.0f} ms, cut {stage['cut'] * 1000:.1f} ms, "
          f"seg {stage['seg'] * 1000:.1f} ms, infer {stage['infer'] * 1000:.1f} ms, "
          f"measured boxes path {infer_ms:.1f} ms")
    json.dump({"results": results, "raster_ms": raster_ms,
               "stage_ms": {k: v * 1000 for k, v in stage.items()}},
              open("/tmp/bench/work/eval_results.json", "w"), indent=1)


main()
