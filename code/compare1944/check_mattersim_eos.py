import numpy as np
from ase.io import read
from mattersim.forcefield import MatterSimCalculator

DATA = "/home/tione/notebook/home/tanshiqian/simpoly_tg_repro/multi_pcff/PE30/data.lmps"
atoms0 = read(DATA, format="lammps-data", style="atomic")
z = np.array([6 if int(t) == 1 else 1 for t in atoms0.get_array("type")])
atoms0.set_atomic_numbers(z)
atoms0.set_pbc(True)
atoms0.wrap()

m = atoms0.get_masses().sum()
calc = MatterSimCalculator(device="cpu", dtype="float32")

print("scale   rho(g/cm3)   E(eV)      E/atom(eV)   P(eV/A3)   P(atm)")
for scale in [0.85, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 1.8, 2.2]:
    a = atoms0.copy()
    a.set_cell(atoms0.get_cell() * scale, scale_atoms=True)
    a.calc = calc
    e = a.get_potential_energy()
    rho = m * 1.66053906660 / a.get_volume()
    try:
        s = a.get_stress(voigt=False, include_ideal_gas=True)
        p = -np.trace(s) / 3.0
    except Exception as ex:
        p = float("nan")
    print(f"{scale:5.2f}  {rho:9.4f}  {e:12.3f}  {e/len(a):9.4f}  {p:10.6f}  {p*160217.663:10.1f}")
