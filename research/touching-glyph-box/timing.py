"""Cost of each option on this host, measured on an otherwise idle machine.

Reports ms per amount box and ms per page for the 154 cells the branch already segments, so the
numbers compare against the branch's own 11.7 ms segmentation and 251.6 ms inference figures.

Run: /tmp/bench/bin/python timing.py
"""
import json
import time

import numpy as np

import common as C
import seg_compare as S

CASES = [(("price", r, c), gt) for (r, c), gt in sorted(C.GT_PRICE.items())] + \
        [(("cash", r, c), gt) for (r, c), gt in sorted(C.GT_CASH.items())]


def measure(fn, n):
    fn()  # warm up
    t = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t) / n * 1000


def main():
    img = C.page()
    inks = {(k, r, c): C.box_mask(img, k, r, c)[0] for (k, r, c), _ in CASES}
    out = {}

    def c_stride(step):
        S.over_segment.__defaults__ = (6, step)

        def run():
            for ink in inks.values():
                S.box_pieces("C", ink)
        return run

    for step in (1, 2, 3):
        ms = measure(c_stride(step), 3)
        out[f"C_stride{step}"] = {"ms_per_box": round(ms / len(inks), 2),
                                  "ms_per_page_154": round(ms / len(inks) * 154, 0)}

    def a_run():
        for ink in inks.values():
            S.box_pieces("A", ink)

    def b_run():
        for ink in inks.values():
            S.box_pieces("B", ink)

    ms = measure(a_run, 5)
    out["A"] = {"ms_per_box": round(ms / len(inks), 3), "ms_per_page_154": round(ms / len(inks) * 154, 0)}
    ms = measure(b_run, 5)
    out["B"] = {"ms_per_box": round(ms / len(inks), 3), "ms_per_page_154": round(ms / len(inks) * 154, 0)}

    # D: one CRNN pass over the whole cell, all 154 cells
    try:
        import eval_models

        crnn = eval_models.load_crnn()

        def d_run_boxes():
            for ink in inks.values():
                eval_models.crnn_read(crnn, eval_models.box_ink_without_rules(ink))

        ms = measure(d_run_boxes, 3)
        out["D"] = {"ms_per_box": round(ms / len(inks), 2),
                    "ms_per_page_154": round(ms / len(inks) * 154, 0),
                    "n_boxes": len(inks)}
    except FileNotFoundError:
        out["D"] = {"error": "crnn.pt not trained yet"}

    print(json.dumps(out, indent=1))
    json.dump(out, open("/tmp/bench/t14/timing.json", "w"), indent=1)


if __name__ == "__main__":
    main()
