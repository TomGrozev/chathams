import json

d = json.load(open("/tmp/bench/work/eval_results.json"))
rows = []


def compose(glyphs):
    if not glyphs:
        return "", None
    maxh = max(g["h"] for g in glyphs)
    out, minp = "", 1.0
    for g in glyphs:
        if g["h"] <= 0.35 * maxh and g["w"] <= 0.35 * maxh and g["area"] < 70:
            out += "."
        else:
            out += g["char"]
        minp = min(minp, g["p"])
    return out, minp


for kind in ("price", "cash"):
    for r in d["results"][kind]:
        pred, minp = compose(r["glyphs"])
        rows.append({"box": f"{kind}:{r['row']},{r['col']}", "gt": r["gt"], "pred": pred,
                     "ok": pred == r["gt"], "minp": minp})
for r in d["results"]["sid"]:
    if r["glyphs"]:
        g = r["glyphs"][0]
        rows.append({"box": f"sid:{r['row']},{r['col']}", "gt": r["gt"], "pred": g["char"],
                     "ok": g["char"] == r["gt"], "minp": g["p"]})
    else:
        rows.append({"box": f"sid:{r['row']},{r['col']}", "gt": r["gt"], "pred": None,
                     "ok": False, "minp": 0.0})

print(len(rows), "boxes scored")
print("total errors", sum(1 for r in rows if not r["ok"]))
for T in (0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 0.99):
    flagged = [r for r in rows if r["minp"] < T]
    caught = sum(1 for r in flagged if not r["ok"])
    false_flags = sum(1 for r in flagged if r["ok"])
    print(f"T={T}: flagged {len(flagged)}/{len(rows)}, errors caught {caught}/"
          f"{sum(1 for r in rows if not r['ok'])}, false flags {false_flags}, "
          f"auto-accepted errors {sum(1 for r in rows if r['ok'] is False and r['minp'] >= T)}")
json.dump(rows, open("/tmp/bench/work/scored_boxes.json", "w"), indent=1)
for r in rows:
    print(r["box"], r["gt"], r["pred"], r["ok"], round(r["minp"], 3))
