import os
import sys

import ase.io
import ase.io.lammpsdata

sys.path.insert(0, "/home/tione/notebook/home/tanshiqian/github/polymer/tg/simpoly/src")
from simpoly.poly_arena import experiment
from simpoly.poly_arena.simulation import protocol, tools

WORK = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(WORK, "build")
os.makedirs(DIR, exist_ok=True)

df = experiment.load_data()
row = df.loc["PS"]
smiles = str(row["smiles"])
caps = (str(row["end_group_0"]), str(row["end_group_1"]))
print("smiles", smiles, "caps", caps, flush=True)

res = protocol.create_lammps_input(
    directory=DIR,
    smiles=smiles,
    end_groups=caps,
    density=0.9,
    temperature=533.0,
    n_tot=1944,
    n_ru_per_chain=10,
    seed=42,
)
print("build result", res, flush=True)

for f in sorted(os.listdir(DIR)):
    p = os.path.join(DIR, f)
    print("FILE", f, os.path.getsize(p) if os.path.isfile(p) else "<dir>", flush=True)

src = os.path.join(DIR, "system.data")
if os.path.exists(src):
    atoms = ase.io.lammpsdata.read_lammps_data(src, atom_style="full", units="real")
    rho = atoms.get_masses().sum() * 1.66053906660 / atoms.get_volume()
    print("system.data atoms", len(atoms), "vol", atoms.get_volume(), "rho", rho, flush=True)
    dst = os.path.join(DIR, "data.lmps")
    types = tools.rewrite_full_to_metal_data(src, dst)
    print("atom_types", types, flush=True)
    a2 = ase.io.read(dst, format="lammps-data", style="atomic")
    rho2 = a2.get_masses().sum() * 1.66053906660 / a2.get_volume()
    print("data.lmps atoms", len(a2), "rho", rho2, "types", sorted(set(a2.arrays["type"])), flush=True)
else:
    print("NO system.data produced", flush=True)
