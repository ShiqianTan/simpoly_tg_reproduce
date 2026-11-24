"""Parse the LAMMPS Tg cooling log into a simpoly stages CSV.

Each `# Stage: cool_XXX_TTTK` block contains a thermo table with columns
Step Temp Density Volume Press ... Density is in g/cm^3. We take the mean/std
of Temp and Density over the last half of each stage's thermo rows.
"""
import argparse
import csv
import re

import numpy as np


def parse(path):
    stages = []
    cur = None
    in_thermo = False
    with open(path) as fh:
        for ln in fh:
            s = ln.strip()
            m = re.match(r"# Stage: (\S+)", s)
            if m:
                if cur and cur["rows"]:
                    stages.append(cur)
                cur = {"name": m.group(1), "rows": []}
                in_thermo = False
                continue
            if s.startswith("Step") and "Temp" in s and "Density" in s:
                in_thermo = True
                continue
            if in_thermo:
                parts = s.split()
                if parts and parts[0].isdigit() and len(parts) >= 3:
                    try:
                        if cur is not None:
                            cur["rows"].append((float(parts[1]), float(parts[2])))
                    except ValueError:
                        in_thermo = False
                else:
                    in_thermo = False
    if cur and cur["rows"]:
        stages.append(cur)
    return stages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="Vivace")
    ap.add_argument("--poly-id", default="PS")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    stages = parse(a.log)
    print(f"parsed {len(stages)} stages")
    rows = []
    for st in stages:
        arr = np.array(st["rows"], dtype=float)
        tail = arr[len(arr) // 2:]
        T_mean, rho_mean = tail[:, 0].mean(), tail[:, 1].mean()
        rows.append({
            "model": a.model,
            "poly_id": a.poly_id,
            "seed": a.seed,
            "temperature_mean": round(T_mean, 4),
            "temperature_std": round(tail[:, 0].std(), 4),
            "density_mean": round(rho_mean, 6),
            "density_std": round(tail[:, 1].std(), 6),
        })
        print(f"  {st['name']:>20}  n={len(arr):4d}  T={T_mean:7.2f}  rho={rho_mean:.4f}")

    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {a.out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
