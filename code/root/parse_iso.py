"""Parse an isothermal-equilibration LAMMPS log.

For every `# Stage: <name>` block it takes the last half of the thermo rows and
reports the mean/std of Temp, Density and Pe, plus a within-stage DRIFT
(mean of the last quarter minus the mean of the third quarter) as an
equilibrium-convergence diagnostic.

Output CSV columns:
    stage, temperature_mean, temperature_std, density_mean, density_std,
    pe_mean, pe_std, rho_drift, pe_drift
"""
import argparse
import csv
import re

import numpy as np


def parse(path):
    stages = []
    cur = None
    idx = None
    with open(path) as fh:
        for ln in fh:
            s = ln.strip()
            m = re.match(r"# Stage: (\S+)", s)
            if m:
                if cur and cur["rows"]:
                    stages.append(cur)
                cur = {"name": m.group(1), "rows": []}
                idx = None
                continue
            if s.startswith("Step") and "Temp" in s and "Density" in s:
                cols = s.split()
                idx = {c: i for i, c in enumerate(cols)}
                continue
            if idx is not None:
                parts = s.split()
                if parts and parts[0].isdigit() and len(parts) >= len(idx):
                    try:
                        row = {c: float(parts[i]) for c, i in idx.items()}
                    except (ValueError, IndexError):
                        idx = None
                        continue
                    if cur is not None:
                        cur["rows"].append(row)
                else:
                    idx = None
    if cur and cur["rows"]:
        stages.append(cur)
    return stages


def stats(vals):
    a = np.array(vals, dtype=float)
    n = len(a)
    tail = a[n // 2:]
    third = a[n // 2: 3 * n // 4]
    last = a[3 * n // 4:]
    drift = (last.mean() - third.mean()) if len(third) and len(last) else 0.0
    return tail.mean(), tail.std(), drift


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = []
    for st in parse(a.log):
        T, Ts, _ = stats([r["Temp"] for r in st["rows"]])
        rho, rhos, drho = stats([r["Density"] for r in st["rows"]])
        pe, pes, dpe = stats([r["PotEng"] for r in st["rows"]])
        rows.append({
            "stage": st["name"],
            "temperature_mean": round(T, 4),
            "temperature_std": round(Ts, 4),
            "density_mean": round(rho, 6),
            "density_std": round(rhos, 6),
            "pe_mean": round(pe, 4),
            "pe_std": round(pes, 4),
            "rho_drift": round(drho, 6),
            "pe_drift": round(dpe, 4),
        })
        print(f"  {st['name']:>20}  T={T:7.2f}  rho={rho:.4f}  drift_rho={drho:+.5f}  pe={pe:.1f}  drift_pe={dpe:+.2f}")

    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {a.out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
