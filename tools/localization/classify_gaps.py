#!/usr/bin/env python3
"""Classify each catalog-missing UI literal as pre-existing (1.3.7) or merge-introduced (1.4.1)."""
import json
import subprocess
import os

import os as _os
REPO = _os.environ.get("COMPOSITOR_CN_REPO") or _os.path.abspath(
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
BASE = "86f15eb"        # CN 1.3.7 baseline (HEAD)
UPSTREAM = "40731947"   # official v1.4.1 snapshot (MERGE_HEAD)

data = json.load(open("/Users/yi/Desktop/AI/DSH/Compositor CN/02-localization/audit-result.json",
                      encoding="utf-8"))
missing = data["missing"]


def present(rev, lit):
    r = subprocess.run(["git", "grep", "-F", "-q", "-e", lit, rev, "--", "Compositor/"],
                       cwd=REPO, capture_output=True)
    return r.returncode == 0


pre, new = [], []
for lit in sorted(missing):
    in_base = present(BASE, lit)
    in_up = present(UPSTREAM, lit)
    rec = {"literal": lit, "sites": len(missing[lit]), "in_1_3_7": in_base, "in_upstream_1_4_1": in_up}
    (pre if in_base else new).append(rec)

print("=" * 72)
print("Gap classification: catalog-missing UI literals")
print("=" * 72)
print(f"pre-existing in 1.3.7 baseline : {len(pre)}")
print(f"introduced by the 1.4.1 merge  : {len(new)}")
print()
print("--- MERGE-INTRODUCED (new English leaks) ---")
for r in new:
    print(f'  "{r["literal"]}"  sites={r["sites"]}  in_upstream={r["in_upstream_1_4_1"]}')
print()
print("--- PRE-EXISTING (carried over from 1.3.7) ---")
for r in pre:
    print(f'  "{r["literal"][:78]}"  sites={r["sites"]}')
print()

json.dump({"pre_existing": pre, "merge_introduced": new},
          open("/Users/yi/Desktop/AI/DSH/Compositor CN/02-localization/gap-classification.json", "w",
               encoding="utf-8"), ensure_ascii=False, indent=2)
