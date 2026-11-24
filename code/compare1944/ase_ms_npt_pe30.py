import sys, time
import numpy as np
from ase import units
from ase.io import read
from ase.md.nvtberendsen import NVTBerendsen
from ase.md.nptberendsen import NPTBerendsen
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary
from ase.optimize import FIRE
from mattersim.forcefield import MatterSimCalculator

DATA = "/home/tione/notebook/home/tanshiqian/simpoly_tg_repro/multi_pcff/PE30/data.lmps"
DEV = sys.argv[1] if len(sys.argv) > 1 else "cuda:3"
NPT = int(sys.argv[2]) if len(sys.argv) > 2 else 3000

atoms = read(DATA, format="lammps-data", style="atomic")
z = np.array([6 if int(t) == 1 else 1 for t in atoms.get_array("type")])
atoms.set_atomic_numbers(z)
atoms.set_pbc(True)
atoms.wrap()
m = atoms.get_masses().sum()


def rho(a):
    return m * 1.66053906660 / a.get_volume()


print(f"# n_atoms={len(atoms)} rho0={rho(atoms):.4f} device={DEV}", flush=True)
calc = MatterSimCalculator(device=DEV, dtype="float32")
atoms.calc = calc

t0 = time.time()
FIRE(atoms, logfile=None).run(fmax=0.5, steps=500)
print(f"# minimize t={time.time()-t0:.1f}s rho={rho(atoms):.4f}", flush=True)

MaxwellBoltzmannDistribution(atoms, temperature_K=700.0, rng=np.random.default_rng(42))
Stationary(atoms)
dyn = NVTBerendsen(atoms, timestep=0.5 * units.fs, temperature_K=700.0, taut=100 * units.fs)
dyn.run(1000)
print(f"# melt700 done t={time.time()-t0:.1f}s rho={rho(atoms):.4f}", flush=True)

dyn = NPTBerendsen(atoms, timestep=1.0 * units.fs, temperature_K=433.0, pressure_au=0.0,
                   taut=100 * units.fs, taup=500 * units.fs, compressibility_au=100.0)


def log():
    p = -atoms.get_stress(voigt=False, include_ideal_gas=True).trace() / 3
    print(f"[npt] t={time.time()-t0:.0f}s step={dyn.get_number_of_steps():5d} "
          f"T={atoms.get_temperature():7.1f} P={p:.5f} rho={rho(atoms):.4f}", flush=True)


dyn.attach(log, interval=100)
dyn.run(NPT)
print(f"# RESULT rho_final={rho(atoms):.4f}", flush=True)
