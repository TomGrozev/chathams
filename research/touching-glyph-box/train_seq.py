"""Train a small CRNN with CTC on synthesised amount strings (option D of ticket #14).

Input: 32 x 128 row canvas, height normalised to 20 px, aspect kept (common.row_normalise).
Output: digit / '.' sequence, unsegmented. Blank class index 11, '.' class index 10.

Run: /tmp/bench/bin/python train_seq.py [steps]
"""
import json
import sys
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

import common as C
import synth

BLANK = 11
N_CLASSES = 12


class CRNN(nn.Module):
    def __init__(self, ch=(16, 32, 64, 64), hidden=96):
        super().__init__()
        c1, c2, c3, c4 = ch
        self.b = nn.Sequential(
            nn.Conv2d(1, c1, 3, padding=1), nn.BatchNorm2d(c1), nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(c1, c2, 3, padding=1), nn.BatchNorm2d(c2), nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(c2, c3, 3, padding=1), nn.BatchNorm2d(c3), nn.ReLU(),
            nn.MaxPool2d((2, 1)),
            nn.Conv2d(c3, c4, 3, padding=1), nn.BatchNorm2d(c4), nn.ReLU(),
            nn.MaxPool2d((2, 1)),
        )
        self.rnn = nn.LSTM(c4 * 2, hidden, num_layers=1, bidirectional=True)
        self.fc = nn.Linear(hidden * 2, N_CLASSES)

    def forward(self, x):
        f = self.b(x)              # B, C, 2, W
        b, c, h, w = f.shape
        f = f.permute(3, 0, 1, 2).reshape(w, b, c * h)
        o, _ = self.rnn(f)
        return self.fc(o)          # T, B, classes


def batch_to_tensor(imgs):
    return torch.cat([C.row_normalise(im, H=32, W=128, scale_h=20) for im in imgs])


def encode(labs):
    return torch.tensor([l for l in labs], dtype=torch.long)


def decode(logits):
    """Greedy CTC decode: argmax per step, collapse repeats, drop blanks."""
    idx = logits.argmax(2)  # T, B
    out = []
    T, B = idx.shape
    for b in range(B):
        seq, prev = [], -1
        for t in range(T):
            k = int(idx[t, b])
            if k != prev and k != BLANK:
                seq.append(k)
            prev = k
        out.append(seq)
    return out


def to_text(seq):
    return "".join("." if k == 10 else str(k) for k in seq)


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 1400
    torch.manual_seed(0)
    rng = np.random.RandomState(0)
    bank = synth.load_bank()
    model = CRNN()
    n_par = sum(p.numel() for p in model.parameters())
    print("params", n_par)
    opt = torch.optim.Adam(model.parameters(), lr=1.5e-3)

    # held-out synthetic set: 400 strings, same generator, different seed
    vrng = np.random.RandomState(999)
    vi, vl = synth.sample_batch(vrng, bank, 400)
    VX = batch_to_tensor(vi)
    Vtgt = torch.tensor([k for l in vl for k in l], dtype=torch.long)
    Vlen = torch.tensor([len(l) for l in vl], dtype=torch.long)

    bs = 64
    t0 = time.perf_counter()
    loss_hist = []
    for step in range(1, steps + 1):
        imgs, labs = synth.sample_batch(rng, bank, bs)
        X = batch_to_tensor(imgs)
        tgt = torch.tensor([k for l in labs for k in l], dtype=torch.long)
        tlen = torch.tensor([len(l) for l in labs], dtype=torch.long)
        logits = model(X)                      # T, B, C
        logp = F.log_softmax(logits, 2)
        T = logp.shape[0]
        inlen = torch.full((bs,), T, dtype=torch.long)
        loss = F.ctc_loss(logp, tgt, inlen, tlen, blank=BLANK, zero_infinity=True)
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        opt.step()
        loss_hist.append(float(loss))
        if step % 50 == 0:
            model.eval()
            with torch.no_grad():
                pred = decode(model(VX))
            ok = sum(1 for p, l in zip(pred, vl) if p == l)
            dt = time.perf_counter() - t0
            print(f"step {step:5d} loss {np.mean(loss_hist[-50:]):.3f} "
                  f"val_seq_acc {ok / len(vl):.3f} {dt:6.1f}s ({dt / step * 1000:.0f} ms/step)",
                  flush=True)
            model.train()
            torch.save(model.state_dict(), "/tmp/bench/t14/crnn.pt")
            if ok / len(vl) >= float(__import__("os").environ.get("T14_TARGET", "0.85")):
                print("early stop at", step, "val_seq_acc", ok / len(vl), flush=True)
                steps = step
                break
    torch.save(model.state_dict(), "/tmp/bench/t14/crnn.pt")
    mem = {}
    mem.update({"steps": steps, "params": n_par,
                "ms_per_step": round((time.perf_counter() - t0) / steps * 1000, 1),
                "val_seq_acc": ok / len(vl), "final_loss": float(np.mean(loss_hist[-50:]))})
    json.dump(mem, open("/tmp/bench/t14/train_seq.json", "w"), indent=1)


if __name__ == "__main__":
    main()
