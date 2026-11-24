"""Diagnose an EMC-built LAMMPS `full` cell: bond lengths, min non-bonded
contacts, chain size (Rg / end-to-end) and box/density.

Usage: python check_cell.py <system.data> [<system.data> ...]
"""
import sys
from collections import defaultdict

import numpy as np

AMU = 1.66053906660


def read_data(path):
    sec = None
    counts = {}
    masses = {}
    atoms = []
    bonds = []
    with open(path) as fh:
        for line in fh:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            low = s.lower()
            if low.endswith(" atoms") or low.endswith(" bonds") or low.endswith(" angles") \
               or low.endswith(" dihedrals") or low.endswith(" impropers") or low.endswith(" types"):
                parts = s.split()
                if len(parts) == 2:
                    counts[parts[1]] = int(parts[0])
                elif len(parts) == 3:
                    counts[parts[1] + "_" + parts[2]] = int(parts[0])
                continue
            if low.endswith("xlo xhi") or low.endswith("ylo yhi") or low.endswith("zlo zhi"):
                counts.setdefault("box", []).append([float(s.split()[0]), float(s.split()[1])])
                continue
            if s in ("Masses", "Atoms", "Bonds", "Angles", "Dihedrals", "Impropers",
                     "Velocities", "Pair Coeffs", "Bond Coeffs"):
                sec = s
                continue
            if sec == "Masses":
                p = s.split()
                if len(p) >= 2 and p[0].isdigit():
                    masses[int(p[0])] = float(p[1])
            elif sec == "Atoms":
                p = s.split()
                if len(p) >= 7:
                    atoms.append((int(p[0]), int(p[1]), int(p[2]), float(p[3]),
                                  float(p[4]), float(p[5]), float(p[6])))
            elif sec == "Bonds":
                p = s.split()
                if len(p) >= 4:
                    bonds.append((int(p[0]), int(p[1]), int(p[2]), int(p[3])))
    return counts, masses, atoms, bonds


def min_image(d, L):
    return d - L * np.round(d / L)


def main(paths):
    for path in paths:
        counts, masses, atoms, bonds = read_data(path)
        if not atoms:
            print(f"{path}: no atoms parsed")
            continue
        L = np.array([b[1] - b[0] for b in counts["box"]])
        pos = np.array([[a[4], a[5], a[6]] for a in atoms])
        typ = np.array([a[2] for a in atoms])
        mol = np.array([a[1] for a in atoms])
        mass = sum(masses.get(t, 0.0) for t in typ)
        vol = float(np.prod(L))
        rho = mass * AMU / vol
        nchains = len(set(mol.tolist()))

        # bonds
        bl = []
        bonded = set()
        for _, _, a, b in bonds:
            d = pos[a - 1] - pos[b - 1]
            bl.append(np.linalg.norm(min_image(d, L)))
            bonded.add((min(a, b), max(a, b)))
        bl = np.array(bl) if bl else np.array([0.0])

        # min non-bonded distance via O(N^2) on a subsample of pairs
        n = len(pos)
        dmin = 1e9
        dmin_pair = None
        # cell list
        rcut = 3.0
        ncell = np.maximum((L / rcut).astype(int), 1)
        cell = {}
        for i in range(n):
            c = tuple((pos[i] / L * ncell).astype(int) % ncell)
            cell.setdefault(c, []).append(i)
        for c, idx in cell.items():
            neigh = []
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        cc = ((c[0] + dx) % ncell[0], (c[1] + dy) % ncell[1], (c[2] + dz) % ncell[2])
                        neigh.extend(cell.get(cc, []))
            for i in idx:
                for j in neigh:
                    if j <= i:
                        continue
                    if (min(i, j) + 1, max(i, j) + 1) in bonded:
                        continue
                    d = np.linalg.norm(min_image(pos[i] - pos[j], L))
                    if d < dmin:
                        dmin = d
                        dmin_pair = (i + 1, j + 1)

        # chain Rg / end-to-end (per chain, using first/last carbon-ish atom by index)
        rgs = []
        for m in sorted(set(mol.tolist())):
            p = pos[mol == m]
            rgs.append(np.sqrt(np.mean(np.sum((p - p.mean(axis=0)) ** 2, axis=1))))
        rgs = np.array(rgs)

        print(f"\n{path}")
        print(f"  atoms={n} chains={nchains} box={L.round(2)} vol={vol:.0f} rho={rho:.4f} g/cm3")
        print(f"  bonds={len(bonds)} len: min={bl.min():.3f} mean={bl.mean():.3f} max={bl.max():.3f}")
        print(f"  min NON-BONDED dist={dmin:.3f} A  pair={dmin_pair}")
        print(f"  chain Rg: mean={rgs.mean():.2f} min={rgs.min():.2f} max={rgs.max():.2f}")


if __name__ == "__main__":
    main(sys.argv[1:])
