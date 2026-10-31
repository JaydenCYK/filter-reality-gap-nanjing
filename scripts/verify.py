# -*- coding: utf-8 -*-
"""
One-command reproducibility check for the filter-reality-gap manuscript.

Usage (from the repo root):
    python scripts/verify.py

What it does:
  1. Runs the three analysis scripts against the corpus (corpus/_user_reviews.txt
     by default, or $UGC_CORPUS).
  2. Compares the freshly generated outputs/ JSON files, field by field,
     against the pre-computed benchmarks in expected_outputs/.
  3. Prints a PASS/FAIL summary.

A full PASS means every number published in the manuscript
(N = 498; sentiment 176/235/87; element frequencies; in-vivo code counts;
 four-dimension union counts 9/24/26/12; platform x dimension cross-tab)
 is reproduced exactly by the open scripts.
"""
import os, json, subprocess, sys

_here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # repo root
BASE = os.environ.get("UGC_BASE", _here)
PY = sys.executable

STEPS = [
    ("clean_and_analyze.py", "ugc_stats.json"),
    ("invivo_stats.py", "invivo_stats.json"),
    ("element_sentiment.py", "element_sentiment.json"),
]

def main():
    env = dict(os.environ); env["UGC_BASE"] = BASE
    ok_all = True
    for script, bench in STEPS:
        out_dir = os.path.join(BASE, "outputs")
        os.makedirs(out_dir, exist_ok=True)
        r = subprocess.run([PY, os.path.join(BASE, "scripts", script)],
                           env=env, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[FAIL] {script} raised an error:")
            print(r.stderr[-2000:])
            ok_all = False
            continue
        new_p = os.path.join(out_dir, bench)
        old_p = os.path.join(BASE, "expected_outputs", bench)
        new = json.load(open(new_p, encoding="utf-8"))
        old = json.load(open(old_p, encoding="utf-8"))
        if new == old:
            print(f"[PASS] {script} -> outputs/{bench} matches the published benchmark exactly.")
        else:
            ok_all = False
            print(f"[FAIL] {script} -> outputs/{bench} differs from expected_outputs/{bench}:")
            for k in old:
                if new.get(k) != old.get(k):
                    print(f"   key '{k}': new={new.get(k)}  expected={old.get(k)}")
    print("-" * 60)
    print("ALL CHECKS PASSED" if ok_all else "CHECKS FAILED — see diff above")
    sys.exit(0 if ok_all else 1)

if __name__ == "__main__":
    main()
