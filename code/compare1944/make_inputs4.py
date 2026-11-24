#!/usr/bin/env python
"""Generate STRICTER cooling-scan LAMMPS inputs (v4) for Vivace / PCFF / MACE-OFF
on the 1944-atom EMC PS cell.

Protocol (stricter than v3):
  minimize -> NVT 700 K melt 20000 -> NPT 533 K pre-equil 20000
  -> 17 NPT cooling stages 533->213 K (step 20 K), 5000 steps/stage
     dt 0.5 fs  (=> 2.5 ps per stage, cooling rate ~8 K/ps)

Writes NEW files in.tg4_* / stages_*_strict.csv ; never touches old data."""
import os

BASE = "/home/tione/notebook/home/tanshiqian/simpoly_tg_repro"
HERE = os.path.join(BASE, "compare1944")
BUILD = os.path.join(BASE, "small_emc", "build")

T_START, T_END, T_STEP = 533, 213, 20
RUN_STEPS = 5000
MELT_STEPS = 20000
PRE_STEPS = 20000
DT = 0.5  # fs

HEADER_VIVACE = f"""# Vivace ML-IAP cooling scan v4 STRICT (melt+quench), 1944-atom EMC PS cell
atom_style      atomic
atom_modify     map array sort 0 2.0
units           metal
newton          on
read_data       {BUILD}/data.lmps
pair_style mliap unified /checkpoints/cueq-0.8.mliap.pt 0
pair_coeff * * C C C H
mass 1 12.010999996910238
mass 2 12.010999996910238
mass 3 12.010999996910238
mass 4 1.0079999997406976
neighbor        0.5 bin
neigh_modify    delay 50 every 2 check yes
thermo_style    custom step temp density vol press ke pe etotal spcpu
thermo_modify   flush yes
thermo          250
timestep        0.0005
fix fMOM all momentum 100 linear 1 1 1 angular
velocity all create 533.0 42 mom yes rot yes dist gaussian
"""

HEADER_PCFF = f"""# PCFF (EMC params) cooling scan v4 STRICT (melt+quench), 1944-atom EMC PS cell
atom_style      full
units           real
newton          on
read_data       {BUILD}/system.data
kspace_style    pppm 1e-4
include         {BUILD}/system.params
neighbor        1.5 bin
neigh_modify    delay 50 every 2 check yes
thermo_style    custom step temp density vol press ke pe etotal spcpu
thermo_modify   flush yes
thermo          250
timestep        0.5
fix fMOM all momentum 100 linear 1 1 1 angular
velocity all create 533.0 42 mom yes rot yes dist gaussian
"""

HEADER_MACEOFF = f"""# MACE-OFF23 medium ML-IAP cooling scan v4 STRICT (melt+quench), 1944-atom EMC PS cell
atom_style      atomic
atom_modify     map array sort 0 2.0
units           metal
newton          on
read_data       {BUILD}/data.lmps
pair_style mliap unified {HERE}/MACE-OFF23_medium-e3nn-mliap_lammps.pt 0
pair_coeff * * C C C H
mass 1 12.010999996910238
mass 2 12.010999996910238
mass 3 12.010999996910238
mass 4 1.0079999997406976
neighbor        0.5 bin
neigh_modify    delay 50 every 2 check yes
thermo_style    custom step temp density vol press ke pe etotal spcpu
thermo_modify   flush yes
thermo          250
timestep        0.0005
fix fMOM all momentum 100 linear 1 1 1 angular
velocity all create 533.0 42 mom yes rot yes dist gaussian
"""


def stages(units: str) -> str:
    if units == "metal":
        tdamp, pdamp = 100 * 0.0005, 1000 * 0.0005   # ps
    else:  # real, dt = 0.5 fs
        tdamp, pdamp = 100 * DT, 1000 * DT           # fs
    blocks = []
    blocks.append("# Minimize\nmin_style cg\nminimize 1e-4 1e-6 1000 10000\n")
    blocks.append(
        "# Melt at 700 K (NVT)\n"
        f"fix melt all nvt temp 700.0 700.0 {tdamp}\nrun {MELT_STEPS}\nunfix melt\n"
    )
    blocks.append(
        "# Pre-equilibration at 533 K (NPT)\n"
        f"fix pre all npt temp 533.0 533.0 {tdamp} aniso 1.000 1.000 {pdamp}\n"
        f"run {PRE_STEPS}\nunfix pre\n"
    )
    temps = list(range(T_START, T_END - 1, -T_STEP))
    for i, T in enumerate(temps):
        blocks.append(
            f"# Stage: cool_{i:03d}_{int(T)}K\n"
            f"fix cool_{i:03d}_{int(T)}K all npt temp {T} {T} {tdamp} aniso 1.000 1.000 {pdamp}\n"
            f"run {RUN_STEPS}\n"
            f"unfix cool_{i:03d}_{int(T)}K\n"
        )
    return "\n".join(blocks)


def write(name: str, header: str, units: str):
    path = os.path.join(HERE, f"in.tg4_{name}")
    with open(path, "w") as f:
        f.write(header + "\n" + stages(units) + "\n")
    print("wrote", path)


if __name__ == "__main__":
    write("vivace", HEADER_VIVACE, "metal")
    write("pcff", HEADER_PCFF, "real")
    write("maceoff", HEADER_MACEOFF, "metal")
    print("temperatures:", list(range(T_START, T_END - 1, -T_STEP)))
    print("melt", MELT_STEPS, "pre", PRE_STEPS, "run", RUN_STEPS,
          "total", MELT_STEPS + PRE_STEPS + 17 * RUN_STEPS)
