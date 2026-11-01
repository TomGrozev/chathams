"""Shared harness code for the touching-glyph-box experiments (ticket #14).

All paths point at /tmp/bench; nothing here is meant to run inside the repo.
"""
import json
import time

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

WORK = "/tmp/bench/work"
PAGE = f"{WORK}/page300.png"
CELLS = json.load(open(f"{WORK}/cells.json"))

# Ground truth, same transcription as docs/research/real-scan-benchmark.md.
GT_PRICE = {(1, 1): "1.5", (1, 2): "2.50", (1, 3): "10.50",
            (3, 1): "7.5", (3, 4): "11", (4, 1): "6.0", (4, 2): "9"}
GT_CASH = {(1, 1): "20"}
GT_SID = {(3, 1): "A", (3, 2): "C", (3, 3): "D", (3, 4): "F", (3, 5): "2", (3, 6): "V", (3, 7): "1",
          (4, 1): "4", (4, 2): "6", (4, 3): "9", (4, 4): "2", (4, 5): "A", (4, 6): "A", (4, 7): "4"}

# The two known joined blobs: (kind, row, col, index-in-blob-order, truth of the pair).
JOINED = [("price", 1, 2, 2, "50"), ("price", 1, 3, 3, "50")]

import os

THREADS = int(os.environ.get("T14_THREADS", "4"))
torch.set_num_threads(THREADS)


def page():
    return cv2.imread(PAGE, cv2.IMREAD_GRAYSCALE)


def box_mask(img, kind, row, col):
    """Return (ink mask uint8 255=ink, grey ROI) for one cell cut-out."""
    for c in CELLS[kind]:
        if (c["row"], c["col"]) == (row, col):
            x0, y0, w, h = c["roi"]
            roi = img[y0:y0 + h, x0:x0 + w]
            _, ink = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            return ink, roi
    raise KeyError((kind, row, col))


def blobs_from_mask(mask, min_area=8, drop_border=True):
    """8-connected components, same filters as eval_pipeline.blobs_from_roi."""
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    out = []
    H, W = mask.shape
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < min_area:
            continue
        if drop_border and (x <= 0 or y <= 0 or x + w >= W or y + h >= H):
            continue
        out.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h), "area": int(area),
                    "mask": (labels[y:y + h, x:x + w] == i).astype(np.uint8) * 255})
    out.sort(key=lambda b: b["x"])
    return out


# ---------------------------------------------------------------- classifiers
class CNN(nn.Module):
    """Same shape as the branch's digits/alnum models."""

    def __init__(self, n_classes):
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


_MODELS = {}


def load_model(name, n_classes):
    if name not in _MODELS:
        m = CNN(n_classes)
        m.load_state_dict(torch.load(f"{WORK}/models/{name}.pt", map_location="cpu"))
        m.eval()
        _MODELS[name] = m
    return _MODELS[name]


def emnist_normalise(mask):
    """Same glyph prep as eval_pipeline.emnist_normalise: longest side to 20 px in 28x28."""
    m = mask.astype(np.uint8)
    ys, xs = np.nonzero(m)
    crop = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = crop.shape
    scale = 20.0 / max(h, w)
    nh, nw = max(1, int(round(h * scale))), max(1, int(round(w * scale)))
    small = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)
    tile = np.zeros((28, 28), np.float32)
    oy, ox = (28 - nh) // 2, (28 - nw) // 2
    tile[oy:oy + nh, ox:ox + nw] = small.astype(np.float32) / 255.0
    return torch.from_numpy(tile).unsqueeze(0).unsqueeze(0)


def row_normalise(mask, H=32, W=128, scale_h=20):
    """Row-style prep for the CRNN: keep aspect, fit height, left-align with 2 px margin.

    The CRNN needs un-squashed glyphs, so unlike the char model the longest side is not
    forced to 20 px; the height is normalised and the width follows the aspect ratio.
    """
    m = mask.astype(np.uint8)
    ys, xs = np.nonzero(m)
    crop = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = crop.shape
    s = scale_h / h
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    if nw > W - 4:
        s2 = (W - 4) / w
        nh, nw = max(1, int(round(h * s2))), W - 4
    small = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)
    tile = np.zeros((H, W), np.float32)
    oy = (H - nh) // 2
    tile[oy:oy + nh, 2:2 + nw] = small.astype(np.float32) / 255.0
    return torch.from_numpy(tile).unsqueeze(0).unsqueeze(0)


def classify(model, mask, classes):
    x = emnist_normalise(mask)
    with torch.no_grad():
        probs = F.softmax(model(x), dim=1)[0]
    p, idx = torch.max(probs, 0)
    return classes[int(idx)], float(p), probs


def logprobs(model, mask, classes):
    """log p per class for one glyph crop (for recognition-based segmentation scores)."""
    x = emnist_normalise(mask)
    with torch.no_grad():
        return F.log_softmax(model(x), dim=1)[0]


class Timer:
    def __init__(self):
        self.ms = 0.0
        self.n = 0

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.ms += (time.perf_counter() - self.t0) * 1000
        self.n += 1


def is_dot(b):
    """The branch's decimal-point rule (compose() in eval_pipeline)."""
    return b["area"] < 70 and b["h"] <= 20 and b["w"] <= 20
