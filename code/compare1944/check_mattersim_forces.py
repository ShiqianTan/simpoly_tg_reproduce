import numpy as np
from ase.io import read
from mattersim.forcefield import MatterSimCalculator

DATA = "/home/tione/notebook/home/tanshiqian/simpoly_tg_repro/multi_pcff/PE30/data.lmps"
DUMP = "/home/tione/notebook/home/tanshiqian/simpoly_tg_repro/compare1944/ms_forces.dump"

# parse lammps dump (single frame)
lines = open(DUMP).read().splitlines()
i = lines.index("ITEM: ATOMS id type x y z fx fy fz")
box = [float(x) for x in lines[5].split()]
natoms = int(lines[3])
rows = [l.split() for l in lines[i + 1: i + 1 + natoms]]
pos_lmp = np.array([[float(r[2]), float(r[3]), float(r[4])] for r in rows])
f_lmp = np.array([[float(r[5]), float(r[6]), float(r[7])] for r in rows])
ids = [int(r[0]) for r in rows]
order = np.argsort(ids)
pos_lmp = pos_lmp[order]
f_lmp = f_lmp[order]
L = box[1]

# ASE
atoms = read(DATA, format="lammps-data", style="atomic")
z = np.array([6 if int(t) == 1 else 1 for t in atoms.get_array("type")])
atoms.set_atomic_numbers(z)
atoms.set_pbc(True)
atoms.wrap()
calc = MatterSimCalculator(device="cpu", dtype="float32")
atoms.calc = calc
e = atoms.get_potential_energy()
f_ase = atoms.get_forces()
pos_ase = atoms.get_positions()

print(f"ASE E={e:.4f} eV   maxF_ase={np.abs(f_ase).max():.5f}   maxF_lmp={np.abs(f_lmp).max():.5f}")
dmax = np.abs(f_ase - f_lmp).max()
print(f"max |F_ase - F_lmp| = {dmax:.6f} eV/A")
print(f"max |dpos| = {np.abs(pos_ase - pos_lmp).max():.4f} A")

# virial pressure from forces (atomic virial, trace)
vol = L ** 3
w_lmp = np.sum(pos_lmp * f_lmp)
w_ase = np.sum(pos_ase * f_ase)
bar = 1.602176634e-19 / 1e-30 / 1e5  # eV/A^3 -> bar
print(f"LAMMPS virial P = {w_lmp / (3 * vol) * bar:.1f} bar")
print(f"ASE    virial P = {w_ase / (3 * vol) * bar:.1f} bar")
try:
    s = atoms.get_stress(voigt=False, include_ideal_gas=False)
    print(f"ASE get_stress virial P = {-np.trace(s)/3*bar:.1f} bar")
except Exception as ex:
    print("get_stress failed:", ex)
