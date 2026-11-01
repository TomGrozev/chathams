"""Train small per-character CNNs on EMNIST (digits, and digits+letters)."""
import json
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.datasets import EMNIST

torch.manual_seed(0)
np.random.seed(0)
torch.set_num_threads(4)

DIGITS_N = 30000
LETTERS_N = 30000
EPOCHS = 3
BATCH = 128


def emnist_images(ds, idx):
    """Return float tensor [n,1,28,28] in [0,1], upright (rot90 k=3 + fliplr)."""
    raw = ds.data[idx].numpy().astype(np.float32) / 255.0
    out = np.empty_like(raw)
    for i in range(raw.shape[0]):
        out[i] = np.fliplr(np.rot90(raw[i], 3))
    return torch.from_numpy(out).unsqueeze(1)


def emnist_labels(ds, idx, offset=0):
    return torch.from_numpy(ds.targets.numpy()[idx].astype(np.int64)) + offset


class CNN(nn.Module):
    def __init__(self, n_classes):
        super().__init__()
        self.c1 = nn.Conv2d(1, 32, 3, padding=1)
        self.c2 = nn.Conv2d(32, 64, 3, padding=1)
        self.fc1 = nn.Linear(64 * 7 * 7, 128)
        self.fc2 = nn.Linear(128, n_classes)

    def forward(self, x):
        x = F.max_pool2d(F.relu(self.c1(x)), 2)
        x = F.max_pool2d(F.relu(self.c2(x)), 2)
        x = F.dropout(x, 0.25, self.training)
        x = x.flatten(1)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, 0.5, self.training)
        return self.fc2(x)


def train_model(Xtr, ytr, Xte, yte, n_classes, name):
    model = CNN(n_classes)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    start = time.process_time()
    n = Xtr.shape[0]
    for epoch in range(EPOCHS):
        perm = torch.randperm(n)
        total = 0.0
        for b in range(0, n, BATCH):
            idx = perm[b:b + BATCH]
            opt.zero_grad()
            logits = model(Xtr[idx])
            loss = F.cross_entropy(logits, ytr[idx])
            loss.backward()
            opt.step()
            total += float(loss) * len(idx)
        model.eval()
        with torch.no_grad():
            acc = (model(Xte).argmax(1) == yte).float().mean().item()
        model.train()
        print(f"{name} epoch {epoch + 1} loss {total / n:.4f} test_acc {acc:.4f}")
    cpu_ms = (time.process_time() - start) * 1000
    torch.save(model.state_dict(), f"/tmp/bench/work/models/{name}.pt")
    print(f"{name} train_cpu_ms {cpu_ms:.0f} classes {n_classes}")
    return model, cpu_ms, acc


import os  # noqa: E402

os.makedirs("/tmp/bench/work/models", exist_ok=True)

dtr = EMNIST("/tmp/bench/data", split="digits", train=True, download=False)
dte = EMNIST("/tmp/bench/data", split="digits", train=False, download=False)
ltr = EMNIST("/tmp/bench/data", split="letters", train=True, download=False)
lte = EMNIST("/tmp/bench/data", split="letters", train=False, download=False)

rng = np.random.RandomState(0)
di = rng.choice(len(dtr), DIGITS_N, replace=False)
li = rng.choice(len(ltr), LETTERS_N, replace=False)
dtei = rng.choice(len(dte), 5000, replace=False)
ltei = rng.choice(len(lte), 5000, replace=False)

t0 = time.process_time()
Xd, yd = emnist_images(dtr, di), emnist_labels(dtr, di)
Xdte, ydte = emnist_images(dte, dtei), emnist_labels(dte, dtei)
print(f"digit tensors ready cpu_ms {(time.process_time() - t0) * 1000:.0f}")

t0 = time.process_time()
Xl, yl = emnist_images(ltr, li), emnist_labels(ltr, li, offset=9)  # letters 1..26 -> 10..35
Xlte, ylte = emnist_images(lte, ltei), emnist_labels(lte, ltei, offset=9)
keep = yl >= 0
keepte = ylte >= 0
Xl, yl, Xlte, ylte = Xl[keep], yl[keep], Xlte[keepte], ylte[keepte]
print(f"letter tensors ready cpu_ms {(time.process_time() - t0) * 1000:.0f}")

results = {}
m1, cpu1, acc1 = train_model(Xd, yd, Xdte, ydte, 10, "digits")
results["digits"] = {"train_cpu_ms": cpu1, "test_acc": acc1, "n_train": int(Xd.shape[0])}

# letters target indices are 1..26; offset 10 gives A=10..Z=35
Xa = torch.cat([Xd, Xl])
ya = torch.cat([yd, yl])
Xate = torch.cat([Xdte, Xlte])
yate = torch.cat([ydte, ylte])
m2, cpu2, acc2 = train_model(Xa, ya, Xate, yate, 36, "alnum")
results["alnum"] = {"train_cpu_ms": cpu2, "test_acc": acc2, "n_train": int(Xa.shape[0])}
json.dump(results, open("/tmp/bench/work/train_results.json", "w"), indent=1)
print("done")
