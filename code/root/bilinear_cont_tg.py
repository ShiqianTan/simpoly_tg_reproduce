"""Constrained continuous bilinear Tg extraction.

Fits a single-kink (continuous) piecewise-linear density-vs-T model:
    rho(T) = c + m_glass*(T - Tb)   for T <= Tb
    rho(T) = c + m_liquid*(T - Tb)  for T >  Tb
and selects the breakpoint Tb minimising the total SSE.  Only breakpoints
whose glassy slope is shallower than the liquid slope (|m_glass| < |m_liquid|,
i.e. the physically correct glass-transition ordering) are accepted.

Usage:  python bilinear_cont_tg.py <csv> [<csv> ...]
"""
import csv
import sys

import numpy as np


def fit_breakpoint(T, rho, Tb):
    # design: [1, (T-Tb) if T<=Tb else 0, (T-Tb) if T>Tb else 0]
    d = T - Tb
    A = np.column_stack([np.ones_like(T), np.where(d <= 0, d, 0.0), np.where(d > 0, d, 0.0)])
    coef, *_ = np.linalg.lstsq(A, rho, rcond=None)
    sse = float(np.sum((rho - A @ coef) ** 2))
    return coef, sse


def fit_one(T, rho):
    order = np.argsort(T)
    T, rho = T[order], rho[order]
    best = None
    for i in range(2, len(T) - 2):
        Tb = T[i]
        coef, sse = fit_breakpoint(T, rho, Tb)
        c, mg, ml = coef
        if not (mg > ml):  # glassy must be shallower (less negative) than liquid
            continue
        if best is None or sse < best[0]:
            best = (sse, Tb, mg, ml, c)
    if best is None:
        # fall back: no sign constraint
        for i in range(2, len(T) - 2):
            Tb = T[i]
            coef, sse = fit_breakpoint(T, rho, Tb)
            if best is None or sse < best[0]:
                best = (sse, Tb, coef[1], coef[2], coef[0])
    return best


def main(paths):
    for path in paths:
        rows = list(csv.DictReader(open(path)))
        seeds = sorted({r["seed"] for r in rows})
        tgs = []
        print(f"\n{path}: n_seeds={len(seeds)}")
        for s in seeds:
            r = [x for x in rows if x["seed"] == s]
            T = np.array([float(x["temperature_mean"]) for x in r])
            rho = np.array([float(x["density_mean"]) for x in r])
            res = fit_one(T, rho)
            if res is None:
                print(f"  seed {s}: fit failed")
                continue
            sse, Tb, mg, ml, c = res
            tgs.append(Tb)
            print(
                f"  seed {s:>3}: Tg_cont={Tb:7.1f} K  "
                f"slope_glass={mg:+.5f}  slope_liquid={ml:+.5f}  sse={sse:.3e}"
            )
        if tgs:
            print(f"{path}: Tg_cont={np.mean(tgs):7.1f} +/- {np.std(tgs):5.1f} K")


if __name__ == "__main__":
    main(sys.argv[1:])
