# Reading a price box whose glyphs touch

Research for [How does the app read a price box whose glyphs touch?](https://github.com/TomGrozev/chathams/issues/14).
Every number below was measured on this host. Nothing here is an implementation.

## Sample and method

Two blobs, both a joined `5` and `0`. They are the only two amount errors in the earlier
benchmark, at 300 dpi, from the same scanned page. Harness: `seg_compare.py`,
`synth.py`, `train_seq.py`, `train_pair.py`, `eval_models.py`, `timing.py`.

| Blob | Box | Size | Aspect | Ink | Min column ink | Max column ink |
|---|---|---|---|---|---|---|
| `price_1_2` | `2.50` | 75 x 58 px | 1.29 | 1006 px | 8 px | 36 px |
| `price_1_3` | `10.50` | 56 x 54 px | 1.04 | 814 px | 4 px | 35 px |

Ground truth is unchanged from
[real-scan-benchmark.md](real-scan-benchmark.md): 6 of 8 amount boxes exact, and both errors are
these two blobs. The other 20 blobs in the 8 amount boxes are single glyphs or a separate
decimal point. All work ran in `/tmp`; no scan pixels, crops or weights are in this branch.

## 1. Options compared

| Option | What it does | Result on this scan |
|---|---|---|
| A | Projection profile, split at the deepest valley, triggered when width / height > 1.15 | Fails both blobs |
| B | Distance transform, marker watershed on the blurred transform | Fails both blobs, wrecks clean boxes |
| C | Over-segmentation over every interior column, the branch CNN scores each partition, one cut costs 0.30 log units | Splits both blobs correctly |
| D | Small CRNN with CTC, trained on synthetic amount strings, reads the box with no split | Undertrained in this run, no box correct |
| E | A 100-class joined-pair head, the branch CNN retrained on synthetic overlapping pairs | Reads both blobs as `70`, confidently |

Published work behind each option:

- Segmentation strategies for handwriting, including the recognition-based family that option C
  belongs to: Casey and Lecolinet, *A survey of methods and strategies in character segmentation*,
  TPAMI 1996, [PDF](https://perso.telecom-paristech.fr/elc/papers/pami96.pdf),
  [DOI](https://doi.org/10.1109/34.506792).
- Foreground and background analysis for touching numeral strings, the family behind option B:
  *Segmentation of single- or multiple-touching handwritten numeral string using background and
  foreground analysis*, TPAMI 2000, [DOI](https://doi.org/10.1109/34.888715).
- Watershed segmentation of numeral strings, and its marker sensitivity:
  [Segmentation of Arabic Handwritten Numeral Strings Based on Watershed Approach](https://publications.waset.org/10010758.pdf).
- Segmentation-free sequence recognition with CTC, the family behind option D: Shi, Bai and Yao,
  [arXiv:1507.05717](https://arxiv.org/abs/1507.05717). "It naturally handles sequences in
  arbitrary lengths, involving no character segmentation".
- Holistic multi-digit recognition without segmentation: Goodfellow et al.,
  [arXiv:1312.6082](https://arxiv.org/abs/1312.6082). 96 % of complete SVHN street numbers and
  97.84 % per digit with an 11-layer network.
- End-to-end handwritten digit string recognition on the Touching Pair, NIST SD19, CAR and CVL
  benchmarks, with CRNN and detector baselines: Hochuli et al.,
  [arXiv:2010.15904](https://arxiv.org/abs/2010.15904). Reported 97 %, 96 % and 84 % recognition
  on NIST-SD19, CAR and CVL. The paper also states that segmentation-free strategies "still show
  some limitations when dealing with a large number of touching digits".
- EMNIST, the training source for every model here: Cohen et al.,
  [arXiv:1702.05373](https://arxiv.org/abs/1702.05373).

## 2. Measured result on the two joined blobs

Split success, composed amount, and CPU cost per box. `ms/box` is the mean over the 8 amount
boxes, PyTorch, 4 threads. Options A, B and C were timed on an idle machine; D and E were timed
while a training job shared the CPU, so those two figures are upper bounds.

| Option | `price_1_2` (75 x 58) | `price_1_3` (56 x 54) | ms/box |
|---|---|---|---|
| A, projection | 3 pieces, `127` | no split (aspect 1.04), `2` | 0.39 |
| B, watershed | 2 pieces, `41` | 2 pieces, `.4` | 0.78 |
| C, recognition-based | 2 pieces, `50`, min p 0.95 | 2 pieces, `50`, min p 0.96 | 31.8 |
| D, CRNN + CTC | `80` | `8` | 3.8 |
| E, pair head | `70` at p 0.881 | `70` at p 0.742 | 1.1 |

Option C found the cut for `price_1_2` at column 35 of 75 and for `price_1_3` at column 28 of 56.
It read `5` at p 0.95 and `0` at p 1.00 on the first, `5` at p 0.96 and `0` at p 1.00 on the
second.

## 3. Clean-box regression

Same 8 amount boxes as the earlier benchmark, which the branch path scores 6 of 8.

| Option | Amount boxes exact | Boxes that changed from correct to wrong |
|---|---|---|
| Branch path today | 6 / 8 | none (baseline) |
| A | 6 / 8 | none, but the two bad boxes change their wrong value |
| B | 1 / 8 | 5 of the 6 correct boxes break |
| C, cut penalty 0.30 | 7 / 8 | none |
| C, cut penalty 0.15 | 7 / 8 | none |
| C, cut penalty 0.50 | 6 / 8 | none, and it misses one join |
| D | 0 / 8 | all (synthetic-only model) |
| E | not applicable | it needs a trigger that says which blob is a pair |

Option C lifts 6 of 8 to 7 of 8. The remaining error is `2.50`, where the leading `2` reads `1`
at p 0.386 in the branch model and then splits into `1` and `1`. That box was already wrong. No
correct box changes.

Cut-penalty sweep, all 8 boxes, cut-candidate stride 1, 2 and 3 give identical readings:

| Penalty | Amount boxes exact | Joined blobs split | Behaviour |
|---|---|---|---|
| 0.00 | 5 / 8 | 2 / 2 | splits clean glyphs |
| 0.15 | 7 / 8 | 2 / 2 | |
| 0.30 | 7 / 8 | 2 / 2 | |
| 0.50 | 6 / 8 | 1 / 2 | misses `price_1_3` |
| 0.75 | 6 / 8 | 1 / 2 | |
| 1.00 | 6 / 8 | 0 / 2 | never splits |

So a penalty between 0.15 and 0.30 works on this page and 0.50 breaks it. One page cannot fix the
value; the useful statement is that the decision needs a prior near 0.3, not 0 and not 1.

## 4. Why the geometric splitters fail here

- **No empty column exists.** On `price_1_2` the lowest column holds 8 ink px against 58 rows, at
  column 53 of 75. The junction is at column 35. The pen crossed the second glyph, so the join is
  a stroke intersection, not a gap.
- **The deepest valley is the wrong one.** Option A splits at the global valley, column 53, then
  again at column 6, and composes `127`.
- **Aspect ratio cannot trigger a split.** `price_1_3` measures 1.04, below any sane aspect
  trigger, and needs a split. `price_1_2` measures 1.29. A width trigger either misses the first
  or admits narrow single glyphs.
- **Distance transform has no usable saddle.** The largest distance is 4.2 px and 3.6 px, because
  the strokes are 4 to 6 px wide at 300 dpi. Blurred peak finding returns 46 and 47 markers on a
  two-glyph blob, so the watershed over-segments inside single strokes.

Option B is dropped on that measurement: it splits clean glyphs (`7.5` to `44`, `11` to `.1`,
`9` to `1`) and keeps only 1 of 8 amount boxes.

## 5. Option C in detail

- Cut candidates: every interior column, at least 6 px from either side. Projection valleys are
  not enough, for the reason in section 4.
- Partitions scored: the whole blob, every one-cut split, and every two-cut split when the blob
  is at least 1.8 times as wide as it is tall.
- Score: sum of the branch CNN's top-1 log probability over the pieces, plus 0.30 per cut. The
  merge decision is therefore the classifier's own evidence, with no second model.
- Cost: 127 forwards of the 28 x 28 CNN for a 75 px wide blob, against 1 forward today. 31.8 ms
  per box on this host, which is 4.9 s for 154 cells. Cut-candidate stride 2 halves the count and
  gives the same readings on this page.

The risk it carries: a single glyph that looks like two gets split. The one case on this page is
the `2` of `2.50`, which the branch model reads `1` at p 0.386 before any splitting. A high
minimum confidence per box, or a rule that refuses to split when the whole-blob reading is
already confident, contains that risk. The flag threshold of T = 0.9 from the earlier benchmark
catches the case.

## 6. Option D: CRNN with CTC

Synthesis: EMNIST digit glyphs pasted at their native scale with a pitch of 0.6 to 1.0 of the
glyph width, so a quarter of the samples overlap heavily, plus rotation, height and baseline
jitter, a rendered decimal point at a third of the glyph height, and Otsu-style binarisation.
Strings of 1 to 5 characters, `.` on 45 % of samples. Harness: `synth.py`.

Model: four convolutional blocks (16, 32, 64, 64 channels), height reduced by 16 and width by 4,
a bidirectional LSTM with 96 hidden units, a 12-class output (10 digits, `.`, blank), CTC loss.
96 k parameters, 0.93 MB. Input 32 x 128, height normalised to 20 px with the aspect kept.

Training cost on this host: 220 to 300 ms per step at batch 64, 4 threads. Validation sequence
accuracy on held-out synthetic strings rose from 0.03 at step 100 to 0.51 at step 700, 0.63 at
step 1350, and 0.695 at the end of the full 2200-step run (581 s of training). Even finished, the
model emits 1 or 2 characters per box (`80` and `8` for the two joins) and gets no real box right:
the synthetic strings do not carry this writer's joins. Inference costs 3.8 ms per box, so cost is
not the blocker; the training data is.

## 7. Option E: a joined-pair head

- 100 classes, class index `10 * a + b`, the branch CNN shape, 28 x 28 input with the longest side
  forced to 20 px, trained on 57 k synthetic pairs at 900 steps. Validation pair accuracy 0.696;
  0.01 is chance.
- On the two real blobs it answers `70` at p 0.881 and p 0.742, and the correct pair `50` is not
  in the top 3 of either. It is confidently wrong, which is worse than an empty answer.
- Cause: at 28 x 28 the branch's own glyph prep squashes a 75 x 58 pair to about 20 x 15 px, so
  the join detail is gone before the first convolution.
- A 32 x 96 aspect-preserving variant did not train: the branch CNN's dense layer expects 64 x 7 x
  7 features, so a wider input needs a different head.

## 8. Can the per-character CNN stay?

- **With option C, yes, unchanged.** The branch CNN is the scoring function; nothing is retrained,
  no new weights ship, and the clean-box result does not move. What changes is the caller: 1
  forward becomes up to roughly 130 per blob, and a cut prior of about 0.3 appears.
- **With option D, no.** It replaces the recognizer rather than adding to it: a new 96 k-parameter
  model, a synthesis pipeline, and a retraining run of hours, memory dependent, per tuning change.
  It also removes the per-glyph probability that the review flag uses today.
- **With option E, no.** It needs retraining, and the retrained model answers the two real joins
  with the wrong pair at 0.74 to 0.88 confidence.

## 9. Docker image and the Elixir path

Measured file sizes: digits model 1.6 MB, alphanumeric model 1.6 MB, CRNN 0.93 MB, pair head
1.7 MB, and the ONNX Runtime wheel for linux x86_64 22.7 MB compressed.

Option C keeps the shipped weights at today's 1.6 MB and adds no runtime dependency. The Elixir
side needs the existing CNN callable in a loop: batch every candidate piece of a box into one
tensor and one forward pass. Either runtime works, because the tensor shapes do not change:
Axon with Nx on the CPU, or Ortex with the model exported to ONNX. Ortex adds the 22.7 MB wheel
(payload larger once unpacked, [INFERENCE]); Axon adds a pure Elixir dependency and no native
binary. A pure Nx run without EXLA on 127 small forward passes per blob is the risk to measure
before commit, because this harness has no Nx numbers.

Option D needs sequence output support: Axon has recurrent layers, and the ONNX export of an LSTM
is standard, so both runtimes can carry it. It uses one forward per box, which is 154 forward
passes per page against roughly 18 000 for option C.

The HTTP sidecar stays as the shape of the cloud option only, behind one interface, and is not
the answer here.

## 10. Recommendation

Keep the per-character CNN and put the recognition-based cut search of option C in front of it,
with a cut prior near 0.3 and the existing T = 0.9 box flag.

What the review flag needs from this option: the per-piece probabilities it already reports, the
whole-blob probability that lost against the split, and the cut columns, so a reviewer can see
that a box was split rather than read.

Limits:

- 2 joined blobs, both `50`, from 1 page. A single `5` against `0` pair exercises one overlap
  shape. Any other pair, and any join at the top rather than the bottom, is unmeasured.
- Zero-shot for option C: the branch CNN is unchanged, and the penalty was chosen on the same 8
  boxes it is scored on. Option C's 7 of 8 is therefore an optimistic number.
- Option D is measured on a model trained only on synthetic strings. Its real cost is a training
  run on real crops, which this page cannot supply.
- Option E was trained to 0.696 pair accuracy only, on 57 k synthetic pairs. The confident wrong
  answer may be a training shortfall, but the 28 x 28 squash is a structural limit that no amount
  of training removes.

## Reproduce

```sh
python -m venv /tmp/bench && /tmp/bench/bin/pip install pymupdf pillow numpy opencv-python-headless
/tmp/bench/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision
mkdir -p /tmp/bench/t14 && cp research/touching-glyph-box/*.py /tmp/bench/t14/
cd /tmp/bench/t14
/tmp/bench/bin/python seg_compare.py    # options A, B, C on both blobs and all 8 boxes
/tmp/bench/bin/python sweep.py          # cut-penalty and stride sensitivity
/tmp/bench/bin/python train_seq.py 2200 # option D
/tmp/bench/bin/python train_pair.py w28 900   # option E
/tmp/bench/bin/python eval_models.py    # D and E on the two blobs and the 8 boxes
/tmp/bench/bin/python timing.py         # cost per box and per page
```

The scripts read the scan from `/tmp/bench/work/page300.png` and write every output to `/tmp`.
