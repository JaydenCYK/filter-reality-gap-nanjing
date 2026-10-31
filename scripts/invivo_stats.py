# -*- coding: utf-8 -*-
"""
Authoritative in-vivo & dimension statistics for SSCI manuscript.
Reuses clean_and_analyze official cleaning + sentiment (N=498 baseline).
Outputs: paper/invivo_stats.json (single source of truth for all numbers)
"""
import re, os, json, importlib.util

_here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # repo root
BASE = os.environ.get("UGC_BASE", _here)
SRC = os.environ.get("UGC_CORPUS", os.path.join(BASE, "corpus", "_user_reviews.txt"))
SCRIPTS = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(BASE, "outputs")
import os as _os; _os.makedirs(OUTDIR, exist_ok=True)
spec = importlib.util.spec_from_file_location("caa", os.path.join(SCRIPTS, "clean_and_analyze.py"))
caa = importlib.util.module_from_spec(spec); spec.loader.exec_module(caa)

# platform boundaries (0-based line index -> platform)
PB = [(0, "Ctrip"), (543, "Ctrip"), (614, "Ctrip"), (705, "Ctrip"),
      (778, "Ctrip"), (791, "Ctrip"), (865, "Xiaohongshu"),
      (899, "Xiaohongshu"), (920, "Xiaohongshu")]

def plat_of(idx):
    p = "unknown"
    for s, x in PB:
        if idx >= s: p = x
    return p

lines = open(SRC, encoding="utf-8").read().splitlines()
recs = []
for i, raw in enumerate(lines):
    s = raw.strip()
    if not s or caa.DATE_RE.search(s) or s in caa.SECTION_HEADERS: continue
    if s in ("点赞", "举报", "1", "2", "3"): continue
    if s.startswith("举报") or s.startswith("关键词："): continue
    recs.append((plat_of(i), s))
seen = set(); out = []
for p, t in recs:
    k = re.sub(r"\s+", "", t)[:120]
    if k in seen: continue
    seen.add(k); out.append((p, t))

total = len(out)
plat = {"Ctrip": 0, "Xiaohongshu": 0}
for p, t in out: plat[p] += 1
sent = {"正面": 0, "中性": 0, "负面": 0}
for p, t in out: sent[caa.sentiment(t)] += 1

FILT = ["滤镜", "精修", "照骗", "原片", "AI", "ai", "P上去", "P图", "纸片人", "磨皮"]
negs = [t for p, t in out if caa.sentiment(t) == "负面"]
filt = [t for p, t in out if p == "Xiaohongshu" and any(w in t for w in FILT)]
subset = list(dict.fromkeys(negs + filt))

# line-level in-vivo phrases -> open codes (real counts in subset)
INVIVO = {
    "AI修图/精修图": ["精修", "AI", "ai", "P图", "滤镜调色"],
    "网上视频/成群鸽子": ["鸽子", "成群"],
    "P上去的": ["P上去", "P 上去"],
    "原片与成片不像": ["原片", "成片", "原图"],
    "纸片人/磨皮": ["纸片人", "磨皮"],
    "排队": ["排队"],
    "动线/混乱/态度": ["动线", "混乱", "态度"],
    "人山人海/人从众": ["人山人海", "人从众", "人太多", "人满"],
    "节假日(十一/国庆/春节)": ["节假日", "十一", "国庆", "春节"],
    "强买强卖/被宰/宰客": ["强买强卖", "强制", "被宰", "宰客", "宰"],
    "再也不来/避雷/大冤种/避坑": ["再也不来", "避雷", "大冤种", "避坑", "再也不"],
    "失望": ["失望"],
    "门票/定价(160/票价/小吃贵)": ["160", "票价", "定价", "门票", "小吃贵"],
    "性价比/不划算/不值": ["性价比", "不划算", "不值"],
}
DIMS = {
    "visual": ["AI修图/精修图", "网上视频/成群鸽子", "P上去的", "原片与成片不像", "纸片人/磨皮"],
    "service": ["排队", "动线/混乱/态度", "人山人海/人从众", "节假日(十一/国庆/春节)", "强买强卖/被宰/宰客"],
    "emotional": ["再也不来/避雷/大冤种/避坑", "失望"],
    "price": ["门票/定价(160/票价/小吃贵)", "性价比/不划算/不值"],
}
line_counts = {k: sum(1 for t in subset if any(w in t for w in v)) for k, v in INVIVO.items()}
dim_union = {}
for d, keys in DIMS.items():
    dim_union[d] = sum(1 for t in subset if any(w in t for k in keys for w in INVIVO[k]))

# ---- platform x dimension cross-tab (for Table 3) ----
def rec_platform(t):
    for p, x in out:
        if x == t:
            return p
    return "unknown"
# build platform-tagged coding subset (preserve which platform each record came from)
tagged = []
seen2 = set()
for p, t in out:
    is_neg = caa.sentiment(t) == "负面"
    is_filt = (p == "Xiaohongshu" and any(w in t for w in FILT))
    if is_neg or is_filt:
        if t in seen2:
            continue
        seen2.add(t); tagged.append((p, t))
def dim_hit(t):
    return [d for d, keys in DIMS.items() if any(w in t for k in keys for w in INVIVO[k])]
xtab = {}
for plat_name in ["Ctrip", "Xiaohongshu"]:
    rows = {}
    for d in DIMS:
        rows[d] = sum(1 for p, t in tagged if p == plat_name and d in dim_hit(t))
    xtab[plat_name] = rows
res = {
    "total": total, "platform": plat, "sentiment": sent,
    "neg_count": len(negs), "filter_count": len(filt),
    "coding_subset_N": len(subset),
    "overlap_neg_and_filter": len(negs) + len(filt) - len(subset),
    "line_counts": line_counts, "dimension_union": dim_union,
    "platform_x_dimension": xtab,
}
outj = os.path.join(OUTDIR, "invivo_stats.json")
json.dump(res, open(outj, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(res, ensure_ascii=False, indent=1))
print("saved:", outj)
