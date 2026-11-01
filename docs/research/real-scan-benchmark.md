# Real-scan benchmark: recognizer accuracy on one filled ledger sheet

Research for [Which recognizer is accurate enough on real scans?](https://github.com/TomGrozev/chathams/issues/9).
All numbers below come from one scanned page. The sample is small: 7 amounts, 1 cash paid box,
2 sids (14 cells). Read every accuracy as a count first.

## Sample and method

- Source: one A4 landscape page, 820 x 580 pt, no text layer, scanned by a phone or flatbed at
  about 300 dpi. Rasterised with PyMuPDF at 300 dpi to a 3417 x 2415 grey image.
- Grid: 8 rows. Each row has 12 free-form price boxes and 2 cash paid boxes. Rows 3 to 8 also have
  a 7-cell sid block. Rows 1 and 2 carry the staff name and a QR code instead.
- Cell finding: threshold grey below 235, keep long horizontal and vertical runs, close, then take
  the white interior components. Price box interiors measure about 157 x 193 px, sid cells about
  89 x 111 px. Harness: `cells2.py`, `build_cells.py`.
- Per box: Otsu threshold inside the cut-out, 8-connected components, components under 8 px
  dropped, components touching the cut-out border dropped (rule fragments). Harness: `segment.py`.
- Recogniser: small CNN (2 conv, 2 dense), trained on EMNIST only, no scan data. Digits model:
  30k EMNIST digits, 3 epochs, EMNIST test accuracy 0.9842. Alphanumeric model: 30k digits plus
  30k letters, 36 classes, 3 epochs, EMNIST test accuracy 0.8634. Harness: `train_cnn.py`,
  `eval_pipeline.py`.
- Glyph prep: tight crop, scale longest side to 20 px, centre in 28 x 28, ink as white, the EMNIST
  convention. A component counts as a decimal point when its height and width are under 0.35 of
  the tallest component and its area is under 70 px.
- Tesseract path: `tesseract.js` (WASM, same LSTM engine as the native build) under Bun, page
  segmentation mode 10 (single character), whitelist `0-9A-Z`. Harness: `tesseract_single_char.js`.
- Everything ran on this host (Linux x64, CPU only). Weights, crops and the scan stayed in
  `/tmp`; none of them is in this branch.

## 1. Ground truth (transcribed from the crops by eye)

| Cell | Value |
|---|---|
| price row 1, box 1 | `1.5` |
| price row 1, box 2 | `2.50` |
| price row 1, box 3 | `10.50` |
| price row 3, box 1 | `7.5` |
| price row 3, box 4 | `11` |
| price row 4, box 1 | `6.0` |
| price row 4, box 2 | `9` |
| cash paid row 1, box 1 | `20` |
| sid row 3 | `A` `C` `D` `F` `2` `V` `1` |
| sid row 4 | `4` `6` `9` `2` `A` `A` `4` |

Two more cells hold small doodle marks, price row 6 box 3 and box 9. They are not amounts and are
excluded from scoring. Every other price and cash box is empty.

## 2. Accuracy

Amounts, CNN digits model, zero shot:

| Box | Truth | Predicted | Exact | Lowest glyph score |
|---|---|---|---|---|
| 1,1 | `1.5` | `1.5` | yes | 0.884 |
| 1,2 | `2.50` | `1.7` | no | 0.383 |
| 1,3 | `10.50` | `10.2` | no | 0.395 |
| 3,1 | `7.5` | `7.5` | yes | 0.902 |
| 3,4 | `11` | `11` | yes | 1.000 |
| 4,1 | `6.0` | `6.0` | yes | 0.568 |
| 4,2 | `9` | `9` | yes | 0.886 |
| cash 1,1 | `20` | `20` | yes | 0.995 |

- Per-box exact: **6 of 8 amounts (75 %)**.
- Per-character: **14 of 23 characters (61 %)**. Method: a box counts its characters only when the
  predicted length equals the truth length; both characters of a merged pair then count wrong.
  That rule is harsh, and the two failures are exactly the merged pairs below.
- Both failures come from segmentation, not from the CNN. Each is one touching glyph pair that
  reached the classifier as one blob.

Sids, CNN alphanumeric model, zero shot:

- **8 of 14 cells exact (57 %)**. Errors: `2` read as `Z` (two cells), `1` as `I`, `4` as `8`,
  `A` as `H`, and one cell (`row 4, col 7`) produced no blob because the glyph touches the cell
  border and the border filter removed it.
- Every misread has a low score (0.213 to 0.874). No high-score error.

Tesseract.js, single character mode, same glyph crops:

- **5 of 14 sid cells exact (36 %)**, **0 of 8 amount boxes exact**.
- 15 of 34 glyph crops came back empty with confidence 0. Single-character mode rejects a crop
  with little margin around the glyph.
- WASM caveat: the engine is the same LSTM, but the WASM build has no multi-threading and no
  adaptive classifier tuning. The empty results look like page segmentation behaviour, not a
  model quality difference, so treat this path as unmeasured rather than proven bad.

Cloud option: **unmeasured**. This repo holds no cloud vision credential, and no data-protection
decision exists for sending staff scans to a cloud model. We did not use an ambient key.

## 3. Segmentation statistics

Expected glyphs count the decimal point as one glyph.

| Box | Truth | Glyphs expected | Blobs found | Note |
|---|---|---|---|---|
| 1,1 | `1.5` | 3 | 3 | dot 16 px |
| 1,2 | `2.50` | 4 | 3 | `5` and `0` touch |
| 1,3 | `10.50` | 5 | 4 | `5` and `0` touch |
| 3,1 | `7.5` | 3 | 3 | dot 24 px |
| 3,4 | `11` | 2 | 2 | a rule fragment was dropped by the border filter |
| 4,1 | `6.0` | 3 | 3 | dot 18 px |
| 4,2 | `9` | 1 | 1 | |
| cash 1,1 | `20` | 2 | 2 | |
| sid cells | 1 char each | 14 | 13 | one glyph touches the cell border |

Totals: 21 amount glyphs produced 19 digit and point blobs; 14 sid glyphs produced 13 blobs.

Failure kinds seen, with counts:

- **Touching glyph pair: 2 of 7 amount boxes.** `5` and `0` join in `2.50` and in `10.50`. Both
  produce a wrong amount and both are the only amount errors.
- **Rule spill into the cut-out: 2 of 7 amount boxes.** One right-edge rule in `10.50` and the
  whole border in `11`. A border filter removes them, at the cost of also dropping a glyph that
  touches the border (1 sid cell lost).
- **Decimal point at the spec-filter limit: 3 of 5 dots.** Dots measure 16 to 24 px. A 20 px
  minimum-area filter keeps 1 of 5, so the filter must not be above about 8 px.
- **Split stroke: 0 seen.** No digit broke into two blobs.
- **Dot merged with a digit: 0 of 5.** Every decimal point is a separate component at 300 dpi.

## 4. Flag rate

22 scored boxes (8 amount, 14 sid). 8 errors. A box is flagged when its lowest glyph score is
below T.

| T | Flagged | Errors caught | Correct boxes flagged | Errors accepted |
|---|---|---|---|---|
| 0.3 | 2 of 22 (9 %) | 2 of 8 | 0 | 6 |
| 0.5 | 5 of 22 (23 %) | 5 of 8 | 0 | 3 |
| 0.7 | 11 of 22 (50 %) | 7 of 8 | 4 | 1 |
| 0.8 | 12 of 22 (55 %) | 7 of 8 | 5 | 1 |
| 0.9 | 16 of 22 (73 %) | 8 of 8 | 8 | 0 |
| 0.95 | 17 of 22 (77 %) | 8 of 8 | 9 | 0 |
| 0.99 | 20 of 22 (91 %) | 8 of 8 | 12 | 0 |

T = 0.9 is the point where every error is flagged, at the cost of flagging 8 correct boxes.
T = 0.5 flags 5 of 8 errors and no correct box.

## 5. Cost on this host

| Stage | Time |
|---|---|
| Rasterise the page at 300 dpi (PyMuPDF) | 1610 ms |
| Cut the cell out of the page image | under 1 ms per cell |
| Threshold and find components | 11.7 ms for 22 boxes |
| CNN inference, one blob at a time | 251.6 ms for 22 boxes |
| Full page, all 154 cells, 147 blobs, warm run | 1429 ms |

Full path per page: about **3.0 s** on a modern x64 CPU, scan to composed amounts. Inference
dominates. Batch inference and a bigger thread count were not tried, so this number is an upper
bound for the design, not a floor.

## 6. Do light grey rules survive Otsu?

- Page-level Otsu threshold on this scan: **196**.
- Rule pixel grey, measured on the box borders: darkest core 148 to 181, most of the anti-aliased
  line 200 to 230.
- With Otsu at 196, the rule lines survive only at their dark parts. Counting separated price and
  cash cell interiors at each threshold:

| Threshold | Cells found (of 112) |
|---|---|
| 200 | 73 |
| 196, Otsu | 73 |
| 196 plus the dilate(5) step in `table_reader.ex` | 100 |
| 210 | 109 |
| 220 | 112 |
| 235 | 112 |
| 245 | 112 |

So the rules are reliably detectable at a fixed threshold of **220** or higher. Otsu alone loses
39 of 112 cells. The dilate(5) step that `lib/chathams/table_reader.ex` already runs recovers 100
of 112, still 12 short.

The current contour cell finder can stay, if its threshold moves from Otsu to a fixed value in the
220 to 235 range (or Otsu plus a floor of 220). The measured cost of keeping Otsu as the only rule
threshold is 12 missing cells per page.

## 7. Recommendation

Keep the CPU per-character CNN as the default recognizer, no cloud option by default, and change
free-form price boxes to the two-part cell variant from ticket 2, because two of seven real
amounts contain touching glyphs that no single-pass component splitter can separate.

Supporting numbers: CNN amounts 6 of 8, sids 8 of 14 with all errors under T = 0.9; Tesseract.js
5 of 14 sids and 0 of 8 amounts, with 15 of 34 crops empty. Sample size 1 page; re-check the
recommendation on 20 to 30 real pages before it is locked.

## Reproduce

```sh
python -m venv /tmp/bench && /tmp/bench/bin/pip install pymupdf pillow numpy opencv-python-headless
/tmp/bench/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision
cd research/real-scan-benchmark
/tmp/bench/bin/python raster.py       # writes /tmp/bench/work/page300.png from the scan
/tmp/bench/bin/python cells2.py       # rule-only cell detection
/tmp/bench/bin/python build_cells.py  # cell lattice
/tmp/bench/bin/python train_cnn.py    # EMNIST digits and alnum models
/tmp/bench/bin/python eval_pipeline.py
```

The scripts read the scan from a path outside this repo and write all output to `/tmp/bench/work`.
