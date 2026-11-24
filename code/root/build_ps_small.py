import os, subprocess, sys
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem

WORK = os.path.dirname(os.path.abspath(__file__))
NCHAIN = 12
NMER = 10

smiles = "CC(c1ccccc1)" * NMER
mol = Chem.MolFromSmiles(smiles)
mol = Chem.AddHs(mol)
print("chain formula:", Chem.rdMolDescriptors.CalcMolFormula(mol),
      "atoms:", mol.GetNumAtoms())
AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
AllChem.MMFFOptimizeMolecule(mol)
Chem.MolToPDBFile(mol, os.path.join(WORK, "ps_chain.pdb"))

natoms_chain = mol.GetNumAtoms()
masses = np.array([a.GetMass() for a in mol.GetAtoms()])
chain_mass = masses.sum()
total_mass = chain_mass * NCHAIN
target_rho = 0.97
L = (total_mass * 1.66053906660 / target_rho) ** (1.0 / 3.0)
L = round(L + 2.0, 2)  # a bit of slack for packmol; NPT will compress
print(f"chain_mass={chain_mass:.2f} total_mass={total_mass:.1f} L={L}")

inp = f"""tolerance 2.0
filetype pdb
output ps_packed.pdb
seed 12345
pbc {L:.3f} {L:.3f} {L:.3f}
"""
for i in range(NCHAIN):
    inp += f"""structure ps_chain.pdb
  number 1
  inside cube 0. 0. 0. {L:.3f}
end structure
"""
open(os.path.join(WORK, "ps_pack.inp"), "w").write(inp)

packmol = os.path.join(os.path.dirname(sys.executable), "packmol")
rc = subprocess.call([packmol], cwd=WORK, stdin=open(os.path.join(WORK, "ps_pack.inp")))
print("packmol rc =", rc)
if rc not in (0, 173):
    sys.exit(1)

# parse packed pdb, build LAMMPS data (atomic, types: 1=C aromatic? keep simple: type 1=C,2=H)
coords = []
types = []
for ln in open(os.path.join(WORK, "ps_packed.pdb")):
    if ln.startswith(("ATOM", "HETATM")):
        el = ln[76:78].strip()
        x, y, z = float(ln[30:38]), float(ln[38:46]), float(ln[46:54])
        coords.append((x, y, z))
        types.append(2 if el == "H" else 1)
coords = np.array(coords)
print("packed atoms:", len(coords), "types:", np.bincount(types))

# center in box
lo = coords.min(0); hi = coords.max(0)
shift = (L - (hi - lo)) / 2 - lo
coords = coords + shift
assert (coords >= 0).all() and (coords <= L).all(), (coords.min(0), coords.max(0))

with open(os.path.join(WORK, "small_ps.data"), "w") as f:
    f.write(f"LAMMPS data file (whole-chain PS {NMER}-mer x{NCHAIN})\n\n")
    f.write(f"{len(coords)} atoms\n2 atom types\n\n")
    f.write(f"0.0 {L:.6f} xlo xhi\n0.0 {L:.6f} ylo yhi\n0.0 {L:.6f} zlo zhi\n\n")
    f.write("Masses\n\n1 12.011\n2 1.008\n\nAtoms # atomic\n\n")
    for i, (c, t) in enumerate(zip(coords, types), 1):
        f.write(f"{i} {t} {c[0]:.6f} {c[1]:.6f} {c[2]:.6f}\n")

rho = total_mass * 1.66053906660 / L**3
print(f"wrote small_ps.data: {len(coords)} atoms, box {L} A, rho={rho:.4f} g/cm3")
