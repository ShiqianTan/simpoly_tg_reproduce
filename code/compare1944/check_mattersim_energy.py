import numpy as np
from ase.io import read
from mattersim.forcefield import MatterSimCalculator

DATA = "/home/tione/notebook/home/tanshiqian/simpoly_tg_repro/multi_pcff/PE30/data.lmps"

atoms = read(DATA, format="lammps-data", style="atomic")
z = np.array([6 if int(t) == 1 else 1 for t in atoms.get_array("type")])
atoms.set_atomic_numbers(z)
atoms.set_pbc(True)
atoms.wrap()

calc = MatterSimCalculator(device="cuda:3", dtype="float32")
atoms.calc = calc
e = atoms.get_potential_energy()
f = atoms.get_forces()
print(f"ASE MatterSim: E={e:.3f} eV  E/atom={e/len(atoms):.4f} eV  maxF={np.abs(f).max():.4f} eV/A")
