"""Compare three splitter families on the two real joined blobs (ticket #14).

A  projection profile + valley detection
B  distance transform + watershed (marker based)
C  over-segmentation + recognition-based merge decision (the branch CNN scores each
   candidate partition; the best-scoring partition wins)

Each method exposes `parse_box(mask) -> list of piece masks` plus the decisions it took.
Run: /tmp/bench/bin/python seg_compare.py
"""
import json
import sys

import cv2
import numpy as np
import torch
import torch.nn.functional as F

import common as C

CLASSES = [str(i) for i in range(10)]
DIG = C.load_model("digits", 10)


# ---------------------------------------------------------------- A: projection
def proj_valleys(m, min_piece=6, smooth=5):
    """Interior columns that are local minima of the smoothed vertical projection."""
    p = (m > 0).sum(0).astype(np.float64)
    k = np.ones(smooth) / smooth
    sm = np.convolve(p, k, "same")
    w = len(sm)
    cand = []
    for x in range(min_piece, w - min_piece):
        lo, hi = max(0, x - 2), min(w, x + 3)
        if sm[x] <= sm[lo:hi].min() + 1e-9:
            cand.append(x)
    # collapse neighbouring candidates to their deepest column
    out, group = [], [cand[0]] if cand else []
    for x in cand[1:]:
        if x - group[-1] <= 1:
            group.append(x)
        else:
            out.append(min(group, key=lambda g: sm[g]))
            group = [x]
    if group:
        out.append(min(group, key=lambda g: sm[g]))
    return out, sm


def split_proj(m, min_piece=6, max_cuts=2, max_ratio=1.15):
    """Split a blob at its deepest interior projection valleys.

    Trigger: a blob is split only when it is wider than `max_ratio` times its height, which
    is the cheap "this might be two glyphs" test available without a classifier.
    """
    h, w = m.shape
    cuts = []
    if w / h <= max_ratio:
        return cuts
    for _ in range(max_cuts):
        cand, sm = proj_valleys(m, min_piece)
        if not cand:
            break
        x = min(cand, key=lambda g: sm[g])
        cuts.append(x)
        # keep splitting only the remaining wide part
        m = m[:, x:]
        min_piece = 6
    return sorted(cuts)


# ---------------------------------------------------------------- B: watershed
def split_watershed(m, min_piece=6, blur=5, frac=0.45):
    """Marker watershed on the inverted distance transform.

    Markers: connected components of the Gaussian-blurred distance transform above
    `frac` of its maximum. The watershed then runs to the saddle between markers.
    """
    m8 = (m > 0).astype(np.uint8)
    dt = cv2.distanceTransform(m8, cv2.DIST_L2, 5)
    dtb = cv2.GaussianBlur(dt, (blur, blur), 0)
    markers = (dtb > frac * dt.max()).astype(np.uint8)
    n, mlab, stats, _ = cv2.connectedComponentsWithStats(markers)
    if n <= 2:
        return [], list(range(1, n))
    bg = (1 - m8).astype(np.uint8)
    if bg.sum() == 0:
        return [], list(range(1, n))
    mlab = mlab + 1  # background becomes label 1
    mlab[bg > 0] = 1
    ws = cv2.watershed(cv2.cvtColor(m8 * 255, cv2.COLOR_GRAY2BGR), mlab.astype(np.int32))
    regions = [i for i in range(2, n + 1)]
    # keep regions that cover a plausible amount of ink
    areas = [(i, int(((ws == i) & (m8 > 0)).sum())) for i in regions]
    areas = [(i, a) for i, a in areas if a >= 30]
    return ws, [i for i, a in areas]


def pieces_from_labels(m, ws, labels):
    out = []
    for i in labels:
        sub = np.where((ws == i) & (m > 0), m, 0).astype(np.uint8)
        ys, xs = np.nonzero(sub)
        if len(ys) == 0:
            continue
        out.append(sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
    return out


# ------------------------------------------------- C: over-segmentation + merge
def over_segment(m, min_piece=6, step=1):
    """Candidate cut columns.

    Projection valleys are NOT enough on this scan: the two real joins are stroke crossings,
    so no column between the glyphs is a local minimum (measured minimum column ink 8 px and
    12 px on a 58-row glyph). Every interior column is a candidate instead.
    """
    w = m.shape[1]
    return list(range(min_piece, w - min_piece + 1, step))


def _batch_logp(masks):
    xs = torch.cat([C.emnist_normalise(mk) for mk in masks])
    with torch.no_grad():
        lp = F.log_softmax(DIG(xs), dim=1)
    best, idx = lp.max(1)
    return best.numpy(), idx.numpy()


CUT_PENALTY = 0.30  # log-prior against an extra cut; 0.30 ~ p=0.74 per cut


def parse_rbs(m, max_cuts=None, penalty=CUT_PENALTY, ret="pieces"):
    """Enumerate partitions of one blob, score each with the char CNN, keep the best.

    Score = sum of per-piece top-1 log probability + penalty * number of cuts. A partition is
    the "merge decision": the pieces found by over-segmentation stay separate only when their
    combined evidence beats reading the blob whole.
    """
    w, h = m.shape[1], m.shape[0]
    cand = over_segment(m)
    if max_cuts is None:
        max_cuts = 2 if w >= 1.8 * h else 1
    combos = [[]]
    if cand:
        combos += [[c] for c in cand]
    if max_cuts >= 2 and len(cand) >= 2:
        for i in range(len(cand)):
            for j in range(i + 1, len(cand)):
                if cand[j] - cand[i] >= 6:
                    combos.append([cand[i], cand[j]])
    # build all pieces once, score in one batch
    all_masks, plan = [], []
    for combo in combos:
        ps = pieces_from_cuts(m, combo)
        if len(ps) != len(combo) + 1:
            plan.append(None)
            continue
        plan.append((combo, list(range(len(all_masks), len(all_masks) + len(ps)))))
        all_masks.extend(ps)
    if not all_masks:
        return {"pieces": [m], "cuts": [], "score": 0.0}
    best_p, best_i = _batch_logp(all_masks)
    scored = []
    for combo, plan_entry in zip(combos, plan):
        if plan_entry is None:
            continue
        _, ii = plan_entry
        s = float(sum(best_p[k] for k in ii)) - penalty * len(combo)
        scored.append((s, combo, ii))
    scored.sort(key=lambda t: -t[0])
    s, combo, ii = scored[0]
    pcs = [all_masks[k] for k in ii]
    if ret == "chars":
        return {"pieces": pcs, "cuts": combo, "score": s,
                "chars": [(CLASSES[int(best_i[k])], float(np.exp(best_p[k]))) for k in ii]}
    return {"pieces": pcs, "cuts": combo, "score": s}


def pieces_from_cuts(m, cuts):
    edges = [0] + sorted(cuts) + [m.shape[1]]
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        sub = np.zeros_like(m)
        sub[:, a:b] = m[:, a:b]
        ys, xs = np.nonzero(sub)
        if len(ys) == 0:
            continue
        out.append(sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
    return out


# ---------------------------------------------------------------- amount compose
def compose(pieces):
    """The branch's own composition rule: dot when short, narrow and under 70 px."""
    if not pieces:
        return "", 1.0
    hs = [p.shape[0] for p in pieces]
    maxh = max(hs)
    out, minp = "", 1.0
    for p in pieces:
        h, w = p.shape
        area = int((p > 0).sum())
        if h <= 0.35 * maxh and w <= 0.35 * maxh and area < 70:
            out += "."
        else:
            ch, pr, _ = C.classify(DIG, p, CLASSES)
            out += ch
            minp = min(minp, pr)
    return out, minp


def box_pieces(method, ink):
    """Run one splitter over one box mask, return (piece list, detail)."""
    blobs = C.blobs_from_mask(ink)
    pieces, detail = [], []
    for b in blobs:
        m = b["mask"]
        if method == "A":
            cuts = split_proj(m)
            ps = pieces_from_cuts(m, cuts)
            detail.append({"w": b["w"], "h": b["h"], "cuts": cuts})
        elif method == "B":
            ws, labels = split_watershed(m)
            ps = pieces_from_labels(m, ws, labels) if labels else [m]
            detail.append({"w": b["w"], "h": b["h"], "regions": len(labels)})
        elif method == "C":
            r = parse_rbs(m)
            ps = r["pieces"]
            detail.append({"w": b["w"], "h": b["h"], "cuts": r["cuts"],
                           "score": round(r["score"], 3)})
        else:
            ps = [m]
            detail.append({"w": b["w"], "h": b["h"]})
        pieces.extend(ps)
    return pieces, detail


def main():
    img = C.page()

    # ---- joined blobs, per method
    out = {"joined": {}, "boxes": {}}
    for kind, row, col, idx, truth in C.JOINED:
        ink, _ = C.box_mask(img, kind, row, col)
        b = C.blobs_from_mask(ink)[idx]
        m = b["mask"]
        key = f"{kind}_{row}_{col}_blob{idx}"
        tmr = {}
        rec = {"truth": truth, "w": b["w"], "h": b["h"], "aspect": round(b["w"] / b["h"], 2)}
        for meth in ("A", "B", "C"):
            t = C.Timer()
            with t:
                for _ in range(20):
                    if meth == "A":
                        ps = pieces_from_cuts(m, split_proj(m))
                    elif meth == "B":
                        ws, labels = split_watershed(m)
                        ps = pieces_from_labels(m, ws, labels) if labels else [m]
                    else:
                        ps = parse_rbs(m)["pieces"]
            amount, minp = compose(ps)
            rec[meth] = {"n_pieces": len(ps), "amount": amount,
                         "min_p": None if not ps else round(minp, 3),
                         "ms": round(t.ms / 20, 3)}
        out["joined"][key] = rec
        print(key, truth, rec)

    # ---- every saved glyph group: the whole-box path, all methods
    for kind, gttab in (("price", C.GT_PRICE), ("cash", C.GT_CASH)):
        for (row, col), truth in sorted(gttab.items()):
            ink, _ = C.box_mask(img, kind, row, col)
            key = f"{kind}_{row}_{col}"
            rec = {"gt": truth}
            for meth in ("A", "B", "C"):
                t = C.Timer()
                with t:
                    for _ in range(10):
                        ps, det = box_pieces(meth, ink)
                amount, minp = compose(ps)
                rec[meth] = {"amount": amount, "ok": amount == truth,
                             "n_pieces": len(ps), "detail": det,
                             "ms": round(t.ms / 10, 3)}
            out["boxes"][key] = rec
            print(key, truth, {m: rec[m]["amount"] for m in ("A", "B", "C")})

    json.dump(out, open("/tmp/bench/t14/seg_compare.json", "w"), indent=1, default=str)
    for meth in ("A", "B", "C"):
        ok = sum(1 for k, v in out["boxes"].items() if v[meth]["ok"])
        print(meth, "amount boxes exact", ok, "/", len(out["boxes"]),
              "mean ms/box", round(np.mean([v[meth]["ms"] for v in out["boxes"].values()]), 2))


if __name__ == "__main__":
    main()
