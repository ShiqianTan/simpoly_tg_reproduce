"""Bilinear (piecewise-linear breakpoint) Tg extraction from a simpoly stages CSV.

Instead of the self-consistent plateau method in cooling_protocol.py, this fits
two straight lines (liquid regime above Tg, glassy regime below Tg) to
density-vs-T and reports the breakpoint that minimises the total residual sum of
squares. It also reports the intersection of the two fitted lines.

Usage:
  python bilinear_tg.py <stages.csv> [<stages.csv> ...]
"""
import csv
import sys
import numpy as np


def read_stages(path):
    rows = []
    with open(path) as fh:
        for row in csv.DictReader(fh):
            rows.append(
                (
                    float(row["seed"]),
                    float(row["temperature_mean"]),
                    float(row["density_mean"]),
                )
            )
    return rows


def fit_line(x, y):
    A = np.vstack([x, np.ones_like(x)]).T
    m, b = np.linalg.lstsq(A, y, rcond=None)[0]
    resid = y - (m * x + b)
    return m, b, float(np.sum(resid ** 2))


def bilinear(T, rho):
    order = np.argsort(T)
    T = np.asarray(T)[order]
    rho = np.asarray(rho)[order]
    n = len(T)
    best = None
    for i in range(3, n - 3):
        Tg = T[i]
        m1, b1, s1 = fit_line(T[:i], rho[:i])
        m2, b2, s2 = fit_line(T[i:], rho[i:])
        sse = s1 + s2
        if best is None or sse < best[0]:
            best = (sse, Tg, m1, b1, m2, b2, i)
    sse, Tg, m1, b1, m2, b2, i = best
    if m1 != m2:
        T_int = (b2 - b1) / (m1 - m2)
    else:
        T_int = Tg
    return Tg, T_int, sse, m1, m2, i


def main(paths):
    for path in paths:
        rows = read_stages(path)
        seeds = sorted({int(s) for s, _, _ in rows})
        per_seed = []
        for s in seeds:
            T = [t for ss, t, _ in rows if int(ss) == s]
            rho = [r for ss, _, r in rows if int(ss) == s]
            if len(T) < 8:
                continue
            Tg, T_int, sse, m1, m2, i = bilinear(T, rho)
            per_seed.append((s, Tg, T_int, m1, m2))
            print(
                f"  seed {s:>3}: breakpoint={Tg:7.1f} K  line_intersection={T_int:7.1f} K  "
                f"slope_glass={m1:+.5f}  slope_liquid={m2:+.5f}"
            )
        if per_seed:
            bps = np.array([p[1] for p in per_seed])
            ints = np.array([p[2] for p in per_seed])
            print(
                f"{path}: n_seeds={len(per_seed)}  Tg_breakpoint={bps.mean():7.1f} +/- {bps.std():5.1f} K"
                f"   Tg_intersection={ints.mean():7.1f} +/- {ints.std():5.1f} K"
            )
        print()


if __name__ == "__main__":
    main(sys.argv[1:])
