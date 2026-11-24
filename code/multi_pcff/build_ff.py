import sys

sys.path.insert(
    0, "/home/tione/notebook/home/tanshiqian/github/polymer/tg/simpoly/src"
)

from simpoly.poly_arena import experiment
from simpoly.poly_arena.generation import wrapper
from simpoly.poly_arena.simulation import protocol, tools

POLY = sys.argv[1]
DENS = float(sys.argv[2]) if len(sys.argv) > 2 else 0.9
N_RU = int(sys.argv[3]) if len(sys.argv) > 3 else 30
N_TOT = int(sys.argv[4]) if len(sys.argv) > 4 else 1944
LABEL = sys.argv[5] if len(sys.argv) > 5 else POLY
SEED = int(sys.argv[6]) if len(sys.argv) > 6 else 42
FIELD = sys.argv[7] if len(sys.argv) > 7 else "compass"

_orig = wrapper.read_emc_template


def patched():
    return _orig().replace("field pcff", f"field {FIELD}")


wrapper.read_emc_template = patched

df = experiment.load_data()
row = df.loc[POLY]
smiles = row["smiles"]
caps = (str(row["end_group_0"]), str(row["end_group_1"]))
print(
    f"POLY {POLY} smiles {smiles} caps {caps} density {DENS} "
    f"n_ru {N_RU} n_tot {N_TOT} seed {SEED} field {FIELD}"
)

directory = f"/home/tione/notebook/home/tanshiqian/simpoly_tg_repro/multi_pcff/{LABEL}"
res = protocol.create_lammps_input(
    directory=directory,
    smiles=smiles,
    end_groups=caps,
    density=DENS,
    temperature=533.0,
    n_tot=N_TOT,
    n_ru_per_chain=N_RU,
    seed=SEED,
)
print("build result", res)

import os

sd = os.path.join(directory, "system.data")
params = os.path.join(directory, "system.params")
for f in ["build.emc", "build.esh", "system.data", "system.params"]:
    p = os.path.join(directory, f)
    print("FILE", f, os.path.getsize(p) if os.path.exists(p) else "MISSING")

with open(params) as fh:
    head = fh.read().splitlines()[:15]
print("---- system.params head ----")
print("\n".join(head))

tools.rewrite_full_to_metal_data(sd, os.path.join(directory, "data.lmps"))

# report atom count / types
from ase.io import read

a = read(os.path.join(directory, "data.lmps"), format="lammps-data", style="atomic")
print("atoms", len(a), "types", sorted(set(a.get_atomic_numbers().tolist())))
