import os
import sys

import ase.io
import ase.io.lammpsdata

sys.path.insert(0, "/home/tione/notebook/home/tanshiqian/github/polymer/tg/simpoly/src")
from simpoly.poly_arena import experiment
from simpoly.poly_arena.simulation import protocol, tools

POLY = sys.argv[1]
LABEL = sys.argv[5] if len(sys.argv) > 5 else POLY
WORK = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(WORK, LABEL)
os.makedirs(DIR, exist_ok=True)

df = experiment.load_data()
row = df.loc[POLY]
smiles = str(row["smiles"])
caps = (str(row["end_group_0"]), str(row["end_group_1"]))
dens = float(sys.argv[2]) if len(sys.argv) > 2 else float(row["density"])
n_ru = int(sys.argv[3]) if len(sys.argv) > 3 else 10
n_tot = int(sys.argv[4]) if len(sys.argv) > 4 else 1944
SEED = int(sys.argv[6]) if len(sys.argv) > 6 else 42
print("POLY", POLY, "smiles", smiles, "caps", caps, "density", dens,
      "n_ru", n_ru, "n_tot", n_tot, "seed", SEED, flush=True)

res = protocol.create_lammps_input(
    directory=DIR,
    smiles=smiles,
    end_groups=caps,
    density=dens,
    temperature=533.0,
    n_tot=n_tot,
    n_ru_per_chain=n_ru,
    seed=SEED,
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
