#!/usr/bin/env python
"""Generate identical 17-stage cooling-scan LAMMPS inputs for Vivace / MACE-OFF / PCFF
on the same 1944-atom EMC-built PS cell. Writes to compare1944/ (does not touch old data)."""
import os

BASE = "/home/tione/notebook/home/tanshiqian/simpoly_tg_repro"
HERE = os.path.join(BASE, "compare1944")
BUILD = os.path.join(BASE, "small_emc", "build")

T_START, T_END, T_STEP = 533, 213, 20
RUN_STEPS = 2000
PRE_STEPS = 4000
DT = 0.5  # fs

HEADER_VIVACE = f"""# Vivace ML-IAP cooling scan, 1944-atom EMC PS cell
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

HEADER_MACEOFF = f"""# MACE-OFF23 medium cooling scan, 1944-atom EMC PS cell
atom_style      atomic
atom_modify     map array sort 0 2.0
units           metal
newton          on
read_data       {BUILD}/data.lmps
pair_style mliap unified {HERE}/MACE-OFF23_medium-mliap_lammps.pt 0
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

HEADER_PCFF = f"""# PCFF (EMC params) cooling scan, 1944-atom EMC PS cell
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
        "# Pre-equilibration at 533 K\n"
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
    path = os.path.join(HERE, f"in.tg_{name}")
    with open(path, "w") as f:
        f.write(header + "\n" + stages(units) + "\n")
    print("wrote", path)


if __name__ == "__main__":
    write("vivace", HEADER_VIVACE, "metal")
    write("maceoff", HEADER_MACEOFF, "metal")
    write("pcff", HEADER_PCFF, "real")
    print("temperatures:", list(range(T_START, T_END - 1, -T_STEP)))
