"""Hyperbolic (Patrone-type) Tg extraction from simpoly stages CSVs.

Model (smooth hyperbolic crossover between glassy and liquid branches):
    rho(T) = rho0 - a*d - b*(0.5*d + sqrt(0.25*d^2 + exp(c))),  d = T - Tg

At T >> Tg the sqrt term -> d, so slope -> (a+b)  (liquid);
at T << Tg the sqrt term -> const, so slope -> a     (glassy).

Fits Tg, rho0, a, b, c by least squares (multi-start on Tg) per seed.

Usage:  python hyperbolic_tg.py <csv> [<csv> ...]
Run with the mace env python (has numpy/scipy).
"""
import csv
import sys

import numpy as np
from scipy.optimize import curve_fit


def patrone(T, Tg, rho0, a, b, c):
    d = T - Tg
    return rho0 - a * d - b * (0.5 * d + np.sqrt(0.25 * d**2 + np.exp(c)))


def fit_one(T, rho):
    best = None
    lo, hi = float(np.min(T)), float(np.max(T))
    span = max(hi - lo, 1.0)
    for frac in np.linspace(0.15, 0.85, 15):
        tg0 = lo + frac * span
        p0 = [tg0, float(np.max(rho)), 2e-4, 3e-4, 0.0]
        try:
            popt, _ = curve_fit(patrone, T, rho, p0=p0, maxfev=200000)
        except Exception:
            continue
        sse = float(np.sum((rho - patrone(T, *popt)) ** 2))
        if best is None or sse < best[0]:
            best = (sse, popt)
    if best is None:
        return None
    Tg, rho0, a, b, c = best[1]
    # drho/dT = -a - b*(...) ; glassy slope -> -a ; liquid slope -> -(a+b)
    return float(Tg), float(-a), float(-(a + b)), best[0]


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
            o = np.argsort(T)
            T, rho = T[o], rho[o]
            res = fit_one(T, rho)
            if res is None:
                print(f"  seed {s}: fit failed")
                continue
            tg, sg, sl, sse = res
            tgs.append(tg)
            print(
                f"  seed {s:>3}: Tg_hyperbolic={tg:7.1f} K  "
                f"slope_glass={sg:+.5f}  slope_liquid={sl:+.5f}  sse={sse:.3e}"
            )
        if tgs:
            print(
                f"{path}: Tg_hyperbolic={np.mean(tgs):7.1f} +/- {np.std(tgs):5.1f} K"
            )


if __name__ == "__main__":
    main(sys.argv[1:])
