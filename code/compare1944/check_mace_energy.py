#!/usr/bin/env python
"""Single-point MACE-OFF23 medium energy on the raw EMC cell, to cross-check the
LAMMPS mliap energy. Run in the `mace` conda env."""
import numpy as np
from ase.io import read
from mace.calculators import mace_off

BASE = "/home/tione/notebook/home/tanshiqian/simpoly_tg_repro"
DATA = BASE + "/small_emc/build/data.lmps"

atoms = read(DATA, format="lammps-data", style="atomic")
types = atoms.get_array("type")
z = np.array([6 if int(t) in (1, 2, 3) else 1 for t in types])
atoms.set_atomic_numbers(z)
atoms.set_pbc(True)
atoms.wrap()

atoms.calc = mace_off(model="medium", device="cpu", default_dtype="float32")
E = atoms.get_potential_energy()
print(f"ASE MACE-OFF23 medium: E={E:.3f} eV  E/atom={E/len(atoms):.4f} eV  natoms={len(atoms)}")
