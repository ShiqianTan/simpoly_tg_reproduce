"""Convert an isothermal-equilibration CSV (parse_iso.py output) into the
simpoly stages-CSV schema expected by the Tg fitters.

Usage: python iso_to_stages.py <iso_csv> <out_csv> <model> <poly_id> [seed] [col]

col = density (default) or pe; `pe` substitutes -pe_mean into the density column
so the same Tg fitters can be applied to the energy-vs-T curve.
"""
import csv
import sys


def main(argv):
    src, dst, model, poly = argv[0], argv[1], argv[2], argv[3]
    seed = argv[4] if len(argv) > 4 else "0"
    col = argv[5] if len(argv) > 5 else "density"
    rows = list(csv.DictReader(open(src)))
    cols = [
        "model",
        "poly_id",
        "seed",
        "temperature_mean",
        "temperature_std",
        "density_mean",
        "density_std",
    ]
    with open(dst, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            if col == "pe":
                d, ds = -float(r["pe_mean"]), r["pe_std"]
            else:
                d, ds = r["density_mean"], r["density_std"]
            w.writerow(
                {
                    "model": model,
                    "poly_id": poly,
                    "seed": seed,
                    "temperature_mean": r["temperature_mean"],
                    "temperature_std": r["temperature_std"],
                    "density_mean": d,
                    "density_std": ds,
                }
            )
    print(f"wrote {dst} ({len(rows)} rows) model={model} poly_id={poly} col={col}")


if __name__ == "__main__":
    main(sys.argv[1:])
