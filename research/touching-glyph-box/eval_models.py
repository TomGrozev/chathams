"""Measure every surviving option on the real joined blobs and on all 8 amount boxes.

Options: C (recognition-based split), D (CRNN+CTC on the whole box), E (joined-pair head,
28x28 branch prep and 32x128 row prep).

Run: /tmp/bench/bin/python eval_models.py
"""
import json
import sys

import numpy as np
import torch
import torch.nn.functional as F

import common as C
import synth
import train_seq
import train_pair

CASES = [(("price", r, c), gt) for (r, c), gt in sorted(C.GT_PRICE.items())] + \
        [(("cash", r, c), gt) for (r, c), gt in sorted(C.GT_CASH.items())]


def load_crnn():
    m = train_seq.CRNN()
    m.load_state_dict(torch.load("/tmp/bench/t14/crnn.pt", map_location="cpu"))
    m.eval()
    return m


def load_pair(prep):
    m = C.CNN(100)
    m.load_state_dict(torch.load(f"/tmp/bench/t14/pair_{prep}.pt", map_location="cpu"))
    m.eval()
    return m


def crnn_read(model, ink, H=32, W=128):
    x = C.row_normalise(ink, H=H, W=W, scale_h=20)
    with torch.no_grad():
        logits = model(x)
    seq = train_seq.decode(logits)[0]
    return train_seq.to_text(seq), logits


def box_ink_without_rules(ink):
    """Drop components that touch the cut-out border (rule spill), keep the rest in place."""
    n, labels, stats, _ = __import__("cv2").connectedComponentsWithStats(ink, connectivity=8)
    H, W = ink.shape
    out = np.zeros_like(ink)
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < 8:
            continue
        if x <= 0 or y <= 0 or x + w >= W or y + h >= H:
            continue
        out[labels == i] = 255
    return out


def main():
    img = C.page()
    crnn = load_crnn()
    paired = {p: load_pair(p) for p in ("w28", "row") if __import__("os").path.exists(
        f"/tmp/bench/t14/pair_{p}.pt")}
    res = {"joined": {}, "boxes": {}}

    # ---------------- joined blobs
    for kind, row, col, idx, truth in C.JOINED:
        ink, _ = C.box_mask(img, kind, row, col)
        b = C.blobs_from_mask(ink)[idx]
        m = b["mask"]
        key = f"{kind}_{row}_{col}_blob{idx}"
        rec = {"truth": truth, "w": b["w"], "h": b["h"]}

        # D on the joined crop
        t = C.Timer()
        with t:
            for _ in range(20):
                txt, _ = crnn_read(crnn, m)
        rec["D"] = {"out": txt, "ok": txt == truth, "ms": round(t.ms / 20, 2)}

        # E on the joined crop
        for prep, model in paired.items():
            x = C.emnist_normalise(m) if prep == "w28" else C.row_normalise(m, H=32, W=96, scale_h=20)
            t = C.Timer()
            with t:
                for _ in range(50):
                    with torch.no_grad():
                        p = F.softmax(model(x), 1)[0]
            top = torch.topk(p, 3)
            pairs = [f"{int(i) // 10}{int(i) % 10}" for i in top.indices.tolist()]
            rec[f"E_{prep}"] = {"top1": pairs[0], "top3": pairs,
                                "p": round(float(top.values[0]), 3),
                                "ok": pairs[0] == truth,
                                "ms": round(t.ms / 50, 3)}
        res["joined"][key] = rec

    # ---------------- all amount boxes
    for (kind, row, col), truth in CASES:
        ink, _ = C.box_mask(img, kind, row, col)
        key = f"{kind}_{row}_{col}"
        rec = {"gt": truth}

        # D on the whole box (rule fragments removed, layout kept)
        whole = box_ink_without_rules(ink)
        t = C.Timer()
        with t:
            for _ in range(10):
                txt, _ = crnn_read(crnn, whole)
        rec["D"] = {"out": txt, "ok": txt == truth, "ms": round(t.ms / 10, 2)}
        rec["D_plain"] = {"out": crnn_read(crnn, ink)[0]}

        # E: pair head on every blob, applied only to blobs that are plausibly a pair
        pairs = []
        for b in C.blobs_from_mask(ink):
            if b["w"] / b["h"] < 0.9:
                continue
            for prep, model in paired.items():
                x = C.emnist_normalise(b["mask"]) if prep == "w28" else C.row_normalise(b["mask"], H=32, W=96, scale_h=20)
                with torch.no_grad():
                    p = F.softmax(model(x), 1)[0]
                i = int(p.argmax())
                pairs.append({"w": b["w"], "h": b["h"], "prep": prep,
                              "pair": f"{i // 10}{i % 10}", "p": round(float(p[i]), 3)})
        rec["E_blobs"] = pairs
        res["boxes"][key] = rec

    json.dump(res, open("/tmp/bench/t14/eval_models.json", "w"), indent=1)

    print("== joined blobs")
    for k, v in res["joined"].items():
        print(k, v["truth"], json.dumps({kk: vv for kk, vv in v.items()
                                         if kk not in ("truth", "w", "h")}))
    print("\n== boxes, option D (whole box, rule fragments dropped)")
    ok = 0
    for k, v in res["boxes"].items():
        ok += bool(v["D"]["ok"])
        print(f"{k:12s} gt={v['gt']:6s} D={v['D']['out']:8s} ok={v['D']['ok']} "
              f"raw={v['D_plain']['out']:8s} ms={v['D']['ms']}")
    print(f"D exact {ok}/{len(res['boxes'])}")


if __name__ == "__main__":
    main()
