import json

GT = {("price", 1, 1): "1.5", ("price", 1, 2): "2.50", ("price", 1, 3): "10.50", ("price", 3, 1): "7.5",
      ("price", 3, 4): "11", ("price", 4, 1): "6.0", ("price", 4, 2): "9", ("cash", 1, 1): "20",
      ("sid", 3, 1): "A", ("sid", 3, 2): "C", ("sid", 3, 3): "D", ("sid", 3, 4): "F",
      ("sid", 3, 5): "2", ("sid", 3, 6): "V", ("sid", 3, 7): "1",
      ("sid", 4, 1): "4", ("sid", 4, 2): "6", ("sid", 4, 3): "9", ("sid", 4, 4): "2",
      ("sid", 4, 5): "A", ("sid", 4, 6): "A", ("sid", 4, 7): "4"}
res = json.load(open("/tmp/bench/work/tess_results.json"))
groups = {}
for r in res:
    groups.setdefault((r["kind"], r["row"], r["col"]), []).append(r["text"])

box_ok = 0
for k, v in sorted(groups.items()):
    pred = "".join(v)
    print(k, "gt", GT[k], "pred", repr(pred), "ok", pred == GT[k])
    box_ok += pred == GT[k]
print("tesseract box exact", box_ok, "/", len(groups))
empty = sum(1 for r in res if r["text"] == "")
print("glyph crops", len(res), "empty outputs", empty)
sid_ok = sum(1 for k, v in groups.items() if k[0] == "sid" and "".join(v) == GT[k])
print("tesseract sid cells exact", sid_ok, "/ 14")
