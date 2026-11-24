#!/usr/bin/env python
"""Generate identical cooling-scan LAMMPS inputs for Vivace / PCFF on the 1944-atom
EMC PS cell, with a Polymatic-style melt + quench pre-equilibration:

  minimize -> NVT 700 K -> NPT 533 K -> 17 NPT cooling stages (533->213 K)

Writes in.tg3_* (does not touch old data)."""
import os

BASE = "/home/tione/notebook/home/tanshiqian/simpoly_tg_repro"
HERE = os.path.join(BASE, "compare1944")
BUILD = os.path.join(BASE, "small_emc", "build")

T_START, T_END, T_STEP = 533, 213, 20
RUN_STEPS = 1500
MELT_STEPS = 10000
PRE_STEPS = 10000
DT = 0.5  # fs

HEADER_VIVACE = f"""# Vivace ML-IAP cooling scan v3 (melt+quench), 1944-atom EMC PS cell
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
thermo_style    custom step temp density vol press ke pe ebond evdwl ecoul elong etotal spcpu
thermo_modify   flush yes
thermo          250
timestep        0.0005
fix fMOM all momentum 100 linear 1 1 1 angular
velocity all create 533.0 42 mom yes rot yes dist gaussian
"""

HEADER_PCFF = f"""# PCFF (EMC params) cooling scan v3 (melt+quench), 1944-atom EMC PS cell
atom_style      full
units           real
newton          on
read_data       {BUILD}/system.data
kspace_style    pppm 1e-4
include         {BUILD}/system.params
neighbor        1.5 bin
neigh_modify    delay 50 every 2 check yes
thermo_style    custom step temp density vol press ke pe ebond evdwl ecoul elong etotal spcpu
thermo_modify   flush yes
thermo          250
timestep        0.5
fix fMOM all momentum 100 linear 1 1 1 angular
velocity all create 533.0 42 mom yes rot yes dist gaussian
"""


def stages(units: str) -> str:
    if units == "metal":
        tdamp, pdamp = 100 * 0.0005, 1000 * 0.0005   # ps
    else:  # real, dt = 0.5 fs
        tdamp, pdamp = 100 * DT, 1000 * DT           # fs
    blocks = []
    blocks.append(
        "# Minimize\n"
        "min_style cg\n"
        "minimize 1e-4 1e-6 1000 10000\n"
    )
    blocks.append(
        "# Melt at 700 K (NVT)\n"
        f"fix melt all nvt temp 700.0 700.0 {tdamp}\n"
        f"run {MELT_STEPS}\n"
        "unfix melt\n"
    )
    blocks.append(
        "# Pre-equilibration at 533 K (NPT)\n"
        f"fix pre all npt temp 533.0 533.0 {tdamp} aniso 1.000 1.000 {pdamp}\n"
        f"run {PRE_STEPS}\n"
        "unfix pre\n"
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
    path = os.path.join(HERE, f"in.tg3_{name}")
    with open(path, "w") as f:
        f.write(header + "\n" + stages(units) + "\n")
    print("wrote", path)


if __name__ == "__main__":
    write("vivace", HEADER_VIVACE, "metal")
    write("pcff", HEADER_PCFF, "real")
    print("temperatures:", list(range(T_START, T_END - 1, -T_STEP)))
    print("melt", MELT_STEPS, "pre", PRE_STEPS, "run", RUN_STEPS)
