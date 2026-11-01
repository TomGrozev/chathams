"""Sensitivity of the recognition-based split (option C) to its one free parameter.

CUT_PENALTY is the log-prior against an extra cut. It is the only knob: the cut search itself is
exhaustive over interior columns. This sweep reports how the composed amounts move with it, and
how a coarser candidate stride changes accuracy and cost.

Run: /tmp/bench/bin/python sweep.py
"""
import json

import numpy as np

import common as C
import seg_compare as S

CASES = [(("price", r, c), gt) for (r, c), gt in sorted(C.GT_PRICE.items())] + \
        [(("cash", r, c), gt) for (r, c), gt in sorted(C.GT_CASH.items())]


def run(penalty, step):
    S.over_segment.__defaults__ = (6, step)
    S.parse_rbs.__defaults__ = (None, penalty, "pieces")
    out = {}
    for (kind, row, col), gt in CASES:
        ink, _ = C.box_mask(C.page(), kind, row, col)
        pieces, _ = S.box_pieces("C", ink)
        amount, _ = S.compose(pieces)
        out[f"{kind}_{row}_{col}"] = {"gt": gt, "out": amount, "ok": amount == gt,
                                      "n_pieces": len(pieces)}
    return out


def main():
    img = C.page()
    res = {}
    for pen in (0.0, 0.15, 0.30, 0.50, 0.75, 1.00):
        for step in (1, 2, 3):
            r = run(pen, step)
            exact = sum(int(v["ok"]) for v in r.values())
            joined_ok = 0
            for kind, row, col, idx, truth in C.JOINED:
                ink, _ = C.box_mask(img, kind, row, col)
                b = C.blobs_from_mask(ink)[idx]
                S.CUT_PENALTY = pen
                ps = S.parse_rbs(b["mask"], penalty=pen)["pieces"]
                amt, _ = S.compose(ps)
                joined_ok += int(amt == truth)
            res[f"pen{pen}_step{step}"] = {"exact": exact, "joined_ok": joined_ok,
                                           "boxes": r,
                                           "splits": {k: v["n_pieces"] for k, v in r.items()}}
            print(f"penalty {pen:.2f} stride {step}: amount boxes exact {exact}/8, "
                  f"joined blobs {joined_ok}/2, pieces per box "
                  f"{[v['n_pieces'] for v in r.values()]}")
            S.CUT_PENALTY = 0.30
    json.dump(res, open("/tmp/bench/t14/sweep.json", "w"), indent=1)
    S.over_segment.__defaults__ = (6, 1)


if __name__ == "__main__":
    main()
