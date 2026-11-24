import numpy as np
from ase.io import read
from mattersim.forcefield import MatterSimCalculator

DATA = "/home/tione/notebook/home/tanshiqian/simpoly_tg_repro/multi_pcff/PE30/data.lmps"
bar = 1.602176634e-19 / 1e-30 / 1e5

atoms = read(DATA, format="lammps-data", style="atomic")
z = np.array([6 if int(t) == 1 else 1 for t in atoms.get_array("type")])
atoms.set_atomic_numbers(z)
atoms.set_pbc(True)
atoms.wrap()
calc = MatterSimCalculator(device="cpu", dtype="float32")
atoms.calc = calc

p0 = -np.trace(atoms.get_stress(voigt=False, include_ideal_gas=True)) / 3
V0 = atoms.get_volume()
print(f"get_stress  P = {p0*bar:12.1f} bar   V0={V0:.2f} A^3  rho0={atoms.get_masses().sum()*1.66053906660/V0:.4f}")

eps = 0.001
Es = {}
for e in (-eps, 0.0, eps):
    a = atoms.copy()
    a.set_cell(atoms.get_cell() * (1 + e), scale_atoms=True)
    a.calc = calc
    Es[e] = a.get_potential_energy()
    print(f"  eps={e:+.4f}  V={a.get_volume():.3f}  E={Es[e]:.5f} eV")
dV = (1 + eps) ** 3 * V0 - (1 - eps) ** 3 * V0
Pfd = -(Es[eps] - Es[-eps]) / dV
print(f"finite-diff P = {Pfd*bar:12.1f} bar")
print(f"ratio fd/stress = {Pfd/p0:.4f}")
