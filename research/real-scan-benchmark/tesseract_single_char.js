const { createWorker } = require("tesseract.js");
const fs = require("fs");

const manifest = JSON.parse(fs.readFileSync("/tmp/bench/work/glyphs.json", "utf8"));

(async () => {
  const worker = await createWorker("eng", 1);
  await worker.setParameters({
    tessedit_pageseg_mode: "10", // single character
    tessedit_char_whitelist: "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
  });
  const out = [];
  for (const g of manifest) {
    const {
      data: { text, confidence },
    } = await worker.recognize(g.path);
    out.push({ ...g, text: text.trim(), conf: confidence });
    console.log(g.kind, g.row, g.col, g.idx, JSON.stringify(text.trim()), "conf", Math.round(confidence));
  }
  fs.writeFileSync("/tmp/bench/work/tess_results.json", JSON.stringify(out, null, 1));
  await worker.terminate();
})();
