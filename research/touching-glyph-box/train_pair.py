"""Option E: a joined-pair head trained on synthetic overlapping glyph pairs.

Two input conventions are trained and compared, because the branch pipeline and a borderline
pair splitter disagree about what a merged blob should look like:

  w28   28 x 28 with the longest side forced to 20 px (common.emnist_normalise, the branch's
        own glyph prep). A pair is squashed to about 20 x 15 here.
  row   32 x 128 with height normalised to 20 px and the aspect kept (common.row_normalise).

The label is the pair as a two-character string, class index 10 * a + b.

Run: /tmp/bench/bin/python train_pair.py [prep] [steps]
"""
import sys
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

import common as C
import synth

PAIR_LABEL = lambda a, b: a * 10 + b  # noqa: E731


def prep_from(imgs, mode):
    if mode == "w28":
        return torch.cat([C.emnist_normalise(im) for im in imgs])
    return torch.cat([C.row_normalise(im, H=32, W=96, scale_h=20) for im in imgs])


def main():
    prep = sys.argv[1] if len(sys.argv) > 1 else "row"
    steps = int(sys.argv[2]) if len(sys.argv) > 2 else 800
    torch.manual_seed(0)
    rng = np.random.RandomState(7)
    bank = synth.load_bank()

    model = C.CNN(100)
    n_par = sum(p.numel() for p in model.parameters())
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    vrng = np.random.RandomState(4242)
    vi, vl = synth.sample_pairs(vrng, bank, 500)
    VX = prep_from(vi, prep)
    Vy = torch.tensor(vl, dtype=torch.long)

    bs = 64
    t0 = time.perf_counter()
    hist = []
    acc = 0.0
    for step in range(1, steps + 1):
        imgs, labs = synth.sample_pairs(rng, bank, bs)
        X = prep_from(imgs, prep)
        y = torch.tensor(labs, dtype=torch.long)
        loss = F.cross_entropy(model(X), y)
        opt.zero_grad()
        loss.backward()
        opt.step()
        hist.append(float(loss))
        if step % 100 == 0:
            model.eval()
            with torch.no_grad():
                acc = (model(VX).argmax(1) == Vy).float().mean().item()
            print(f"step {step:4d} loss {np.mean(hist[-100:]):.3f} val_pair_acc {acc:.3f} "
                  f"{(time.perf_counter() - t0):.0f}s", flush=True)
            model.train()

    torch.save(model.state_dict(), f"/tmp/bench/t14/pair_{prep}.pt")
    import json

    json.dump({"prep": prep, "steps": steps, "params": n_par, "val_pair_acc": acc,
               "ms_per_step": round((time.perf_counter() - t0) / steps * 1000, 1),
               "final_loss": float(np.mean(hist[-100:]))},
              open(f"/tmp/bench/t14/train_pair_{prep}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
