"""Synthesise handwritten amount strings (and joined pairs) from EMNIST digits.

The rendered strings copy the conventions of the real scan: Otsu-binarised ink, stroke width
about a tenth of the glyph height, and a horizontal pitch below 1.0 so adjacent glyphs overlap
and their strokes cross. That overlap is the only way the model sees a joined pair, because the
scan itself cannot be used as training data.

The decimal point is rendered small and low, as in the scan (16 to 24 px against a 54 to 58 px
glyph height, i.e. about a third of the height).
"""
import cv2
import numpy as np

DIGITS = None


def load_glyphs(path="/tmp/bench/data"):
    """EMNIST digits train split as (images uint8 0..255, labels)."""
    from torchvision.datasets import EMNIST

    d = EMNIST(path, split="digits", train=True, download=False)
    x = np.asarray(d.data, dtype=np.uint8)  # already 255 = ink
    y = np.asarray(d.targets, dtype=np.int64)
    return x, y


def _glyph_bank(x, y):
    return [x[y == d] for d in range(10)]


def _paste(canvas, g, x0, y0):
    h, w = g.shape
    H, W = canvas.shape
    xs0, ys0 = max(0, x0), max(0, y0)
    xs1, ys1 = min(W, x0 + w), min(H, y0 + h)
    if xs1 <= xs0 or ys1 <= ys0:
        return
    sub = g[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0]
    canvas[ys0:ys1, xs0:xs1] = np.maximum(canvas[ys0:ys1, xs0:xs1], sub)


def _rotate(g, deg):
    if abs(deg) < 0.5:
        return g

    h, w = g.shape
    m = cv2.getRotationMatrix2D((w / 2, h / 2), deg, 1.0)
    return cv2.warpAffine(g, m, (w, h), flags=cv2.INTER_LINEAR, borderValue=0)


def render_string(rng, bank, text, height=None, pitch=None, jitter=2, rot=6.0):
    """Render `text` (digits and '.') as a binary ink image, ink 255 on black.

    Glyph ink height is `height` px (20 to 27 by default), which is the native EMNIST scale, so
    upscaling does not thicken the strokes. `pitch` is the advance as a fraction of the glyph
    width: below 1.0 the glyphs overlap, which is what produces a joined pair.

    Returns the ink image cropped to its bounding box, uint8, 255 = ink.
    """
    height = int(rng.randint(20, 28)) if height is None else height
    n = len(text)
    placed = []
    for i, ch in enumerate(text):
        if ch == ".":
            gh = max(2, int(round(height * rng.uniform(0.13, 0.20))))
            gw = max(2, int(round(height * rng.uniform(0.08, 0.13))))
            g = np.full((gh, gw), 255, np.uint8)
            placed.append({"img": g, "w": gw, "bottom_low": 0})
            continue
        for _ in range(6):
            g0 = bank[int(ch)][int(rng.randint(len(bank[int(ch)])))]
            ys0, xs0 = np.nonzero(g0 > 80)
            if len(ys0) and ys0.max() - ys0.min() >= 18:
                break
        ys0, xs0 = np.nonzero(g0 > 80)
        gh_src = ys0.max() - ys0.min() + 1
        s = height / gh_src
        lh, lw = max(4, int(round(g0.shape[0] * s))), max(4, int(round(g0.shape[1] * s)))
        g = cv2.resize(g0.astype(np.float32) / 255.0, (lw, lh), interpolation=cv2.INTER_AREA)
        g = _rotate(g, rng.uniform(-rot, rot))
        g = np.clip(g * 255, 0, 255).astype(np.uint8)
        ysb, xsb = np.nonzero(g > 80)
        if len(ysb) == 0:
            continue
        g = g[ysb.min():ysb.max() + 1, xsb.min():xsb.max() + 1]
        placed.append({"img": g, "w": g.shape[1], "bottom_low": 0})
    if not placed:
        placed = [{"img": np.full((height, height), 255, np.uint8), "w": height}]
    pitches = [rng.uniform(0.60, 1.0) if pitch is None else pitch for _ in range(len(placed))]
    adv = [int(round(p["w"] * pitches[i])) for i, p in enumerate(placed[:-1])]
    adv.append(placed[-1]["w"])
    W = int(sum(adv) + 16)
    H = int(height * 2.2)
    canvas = np.zeros((H, W), np.uint8)
    base = int(H * 0.72)
    x = 8
    for i, p in enumerate(placed):
        g = p["img"]
        y = base - g.shape[0] + int(rng.randint(-jitter, jitter + 1))
        if p["w"] <= max(3, int(height * 0.15)):
            # a decimal point sits on the baseline
            y = base - g.shape[0] - int(round(height * rng.uniform(0.02, 0.08)))
        _paste(canvas, g, x, y)
        x += adv[i]
    ys, xs = np.nonzero(canvas > 80)
    if len(ys) == 0:
        return np.zeros((height, max(8, W // 2)), np.uint8)
    out = (canvas[ys.min():ys.max() + 1, xs.min():xs.max() + 1] > 80).astype(np.uint8) * 255
    return out


def sample_text(rng, maxlen=5, p_dot=0.45):
    n = int(rng.choice([1, 2, 2, 3, 3, 4, 4, 5], p=None)) if maxlen >= 5 else int(rng.randint(1, maxlen + 1))
    n = max(1, min(n, maxlen))
    digits = [str(int(rng.randint(10))) for _ in range(n)]
    if rng.rand() < p_dot and n >= 2:
        pos = 1 if n >= 3 else 1
        digits = digits[:pos] + ["."] + digits[pos:]
    return "".join(digits), digits


def sample_batch(rng, bank, bs, maxlen=5, p_dot=0.45, pitch=None):
    """Return (list of ink images, list of label lists)."""
    imgs, labs = [], []
    for _ in range(bs):
        _, chars = sample_text(rng, maxlen, p_dot)
        p = pitch
        if p is None:
            # a quarter of the samples are strongly overlapped, as in the joined pairs
            p = rng.uniform(0.55, 0.72) if rng.rand() < 0.35 else rng.uniform(0.70, 1.0)
        imgs.append(render_string(rng, bank, "".join(chars), pitch=p))
        labs.append([10 if c == "." else int(c) for c in chars])
    return imgs, labs


def sample_pairs(rng, bank, bs, overlap=True):
    """Two-glyph renders for the pair classifier: label = 10 * a + b."""
    imgs, labs = [], []
    for _ in range(bs):
        a, b = int(rng.randint(10)), int(rng.randint(10))
        p = rng.uniform(0.5, 0.68) if overlap else rng.uniform(0.75, 1.0)
        imgs.append(render_string(rng, bank, f"{a}{b}", height=int(rng.randint(44, 60)), pitch=p))
        labs.append(a * 10 + b)
    return imgs, labs


def load_bank():
    global DIGITS
    if DIGITS is None:
        x, y = load_glyphs()
        DIGITS = _glyph_bank(x, y)
    return DIGITS
