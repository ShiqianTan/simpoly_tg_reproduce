#!/usr/bin/env python
"""Vivace ASE cooling scan on the 1944-atom EMC PS cell.

Runs in the simpoly env with PYTHONPATH=<repo>/src.
Protocol mirrors the LAMMPS in.tg3_* inputs:
  minimize (FIRE) -> NVT 700 K melt -> NPT 533 K pre-equil
  -> 17 NPT cooling stages 533->213 K (step 20 K), 1500 steps/stage,
     dt 0.5 fs, Tdamp 50 fs, Pdamp 500 fs.
"""
import argparse
import os
import time

import numpy as np
from ase import units
from ase.io import read
from ase.md.nptberendsen import NPTBerendsen
from ase.md.nvtberendsen import NVTBerendsen
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary
from ase.optimize import FIRE

BASE = "/home/tione/notebook/home/tanshiqian/simpoly_tg_repro"
HERE = os.path.join(BASE, "compare1944")
DATA = os.path.join(BASE, "small_emc", "build", "data.lmps")
MODEL = "/home/tione/notebook/home/tanshiqian/github/polymer/tg/simpoly/checkpoints/vivace_v0.1.pt"


def load_atoms():
    atoms = read(DATA, format="lammps-data", style="atomic")
    types = atoms.get_array("type") if "type" in atoms.arrays else None
    if types is not None:
        z = np.array([6 if int(t) in (1, 2, 3) else 1 for t in types])
        atoms.set_atomic_numbers(z)
    atoms.set_pbc(True)
    atoms.wrap()
    return atoms


def rho(atoms):
    return atoms.get_masses().sum() * 1.66053906660 / atoms.get_volume()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--steps", type=int, default=1500)
    p.add_argument("--melt", type=int, default=10000)
    p.add_argument("--pre", type=int, default=10000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--tag", default="vivace_ase")
    p.add_argument("--out", default=os.path.join(HERE, "stages_vivace_ase.csv"))
    args = p.parse_args()

    from simpoly.vivace.calculator import MLFFCalculator

    log = open(os.path.join(HERE, f"tg_{args.tag}.log"), "w")

    def emit(s):
        print(s, flush=True)
        log.write(s + "\n")
        log.flush()

    atoms = load_atoms()
    emit(f"# {len(atoms)} atoms, rho0={rho(atoms):.4f} g/cm3, cell={atoms.cell.lengths()}")

    atoms.calc = MLFFCalculator(MODEL)

    dt = 0.5 * units.fs
    taut = 50 * units.fs
    taup = 500 * units.fs
    comp = 100.0  # Angstrom^3 / eV

    t0 = time.time()
    FIRE(atoms, logfile=None).run(fmax=0.5, steps=1000)
    emit(f"# minimize done t={time.time()-t0:.1f}s rho={rho(atoms):.4f}")

    MaxwellBoltzmannDistribution(atoms, temperature_K=533.0, rng=np.random.default_rng(args.seed))
    Stationary(atoms)

    def run_nvt(T, steps, label):
        dyn = NVTBerendsen(atoms, timestep=dt, temperature_K=T, taut=taut)
        t0 = time.time()
        dyn.run(steps)
        wall = time.time() - t0
        emit(f"# {label}: T={atoms.get_temperature():.2f} rho={rho(atoms):.5f} s/step={wall/steps:.4f}")

    emit("# Melt at 700 K (NVT)")
    run_nvt(700.0, args.melt, "melt_700K")

    def run_stage(T, steps, label):
        dyn = NPTBerendsen(
            atoms, timestep=dt, temperature_K=T, pressure_au=0.0,
            taut=taut, taup=taup, compressibility_au=comp,
        )
        samples = []

        def sample():
            samples.append((atoms.get_temperature(), rho(atoms)))

        dyn.attach(sample, interval=20)
        t0 = time.time()
        dyn.run(steps)
        wall = time.time() - t0
        arr = np.array(samples)
        half = arr[len(arr) // 2:]
        Tm, Ts = half[:, 0].mean(), half[:, 0].std()
        Rm, Rs = half[:, 1].mean(), half[:, 1].std()
        ns_per_day = steps * (dt / units.fs) * 1e-6 * 86400 / wall
        emit(f"# Stage: {label}\n[{label}] T={Tm:.2f} rho={Rm:.5f} s/step={wall/steps:.4f} ns/day={ns_per_day:.4f}")
        return Tm, Ts, Rm, Rs

    rows = []
    emit("# Pre-equilibration at 533 K (NPT)")
    run_stage(533.0, args.pre, "pre_533K")
    for i, T in enumerate(range(533, 213 - 1, -20)):
        label = f"cool_{i:03d}_{T}K"
        Tm, Ts, Rm, Rs = run_stage(float(T), args.steps, label)
        rows.append((Tm, Ts, Rm, Rs))

    with open(args.out, "w") as f:
        f.write("model,poly_id,seed,temperature_mean,temperature_std,density_mean,density_std\n")
        for Tm, Ts, Rm, Rs in rows:
            f.write(f"vivace_ase,PS,{args.seed},{Tm:.4f},{Ts:.4f},{Rm:.6f},{Rs:.6f}\n")
    emit(f"# wrote {args.out}")
    log.close()


if __name__ == "__main__":
    main()
