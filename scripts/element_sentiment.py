# -*- coding: utf-8 -*-
"""
Per-element dominant-sentiment statistics for Table 1.
Reuses clean_and_analyze official ELEMENTS + sentiment + cleaning (same N=498
baseline), so this is fully reproducible from the raw corpus.

For each of the 8 element dimensions, count the de-duplicated records that hit
the element (same rule as the element-frequency column), then within that
per-element subset count positive / neutral / negative and report the
dominant category. A record may hit several elements; each element's column
is computed independently on its own hitting subset.
"""
import os, json, importlib.util

_here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # repo root
BASE = os.environ.get("UGC_BASE", _here)
SRC = os.environ.get("UGC_CORPUS", os.path.join(BASE, "corpus", "_user_reviews.txt"))
SCRIPTS = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(BASE, "outputs")
import os as _os; _os.makedirs(OUTDIR, exist_ok=True)
spec = importlib.util.spec_from_file_location("caa", os.path.join(SCRIPTS, "clean_and_analyze.py"))
caa = importlib.util.module_from_spec(spec); spec.loader.exec_module(caa)

recs = caa.load_records(SRC)

MAP = {"正面": "positive", "中性": "neutral", "负面": "negative"}
# stable tie-break order (if two categories tie, prefer in this order)
PREF = ["negative", "positive", "neutral"]

res = {}
for k, kws in caa.ELEMENTS.items():
    hits = [r for r in recs if any(w in r for w in kws)]
    dist = {"positive": 0, "neutral": 0, "negative": 0}
    for r in hits:
        dist[MAP[caa.sentiment(r)]] += 1
    n = len(hits)
    # pick the category with the highest count; ties broken by PREF order
    dominant = ""
    if n:
        m = max(dist.values())
        candidates = [c for c in PREF if dist[c] == m]
        dominant = candidates[0]
    res[k] = {
        "n": n,
        "dist": dist,
        "dominant": dominant,
        "dominant_share": round(dist[dominant] / n * 100, 1) if n else 0.0,
    }

out = os.path.join(OUTDIR, "element_sentiment.json")
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
for k in sorted(res, key=lambda x: -res[x]["n"]):
    d = res[k]
    print(f"{k}: n={d['n']}  pos {d['dist']['positive']} / neu {d['dist']['neutral']} / neg {d['dist']['negative']}  -> {d['dominant'].upper()} ({d['dominant_share']}%)")
print("saved:", out)
