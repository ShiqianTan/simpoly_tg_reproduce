#!/usr/bin/env python
"""Generate the SHORTENED MACE-OFF cooling scan (in.tg4_maceoff_short) on the
1944-atom EMC PS cell, because MACE mliap is ~0.97 s/step (~20x slower than
Vivace). Protocol identical in shape to in.tg4_maceoff but with
  minimize -> NVT 700 K melt 5000 -> NPT 533 K pre 5000
  -> 17 NPT stages 533->213 K (step 20 K), 1250 steps/stage
     dt 0.5 fs  (=> 0.625 ps per stage)
Uses the float32 cueq mliap model (2x faster than float64).
Writes NEW file; never touches old data."""
import os

BASE = "/home/tione/notebook/home/tanshiqian/simpoly_tg_repro"
HERE = os.path.join(BASE, "compare1944")
BUILD = os.path.join(BASE, "small_emc", "build")

T_START, T_END, T_STEP = 533, 213, 20
RUN_STEPS = 1250
MELT_STEPS = 5000
PRE_STEPS = 5000
DT = 0.5  # fs

HEADER = f"""# MACE-OFF23 medium (float32 cueq) ML-IAP cooling scan v4 SHORT, 1944-atom EMC PS cell
atom_style      atomic
atom_modify     map array sort 0 2.0
units           metal
newton          on
read_data       {BUILD}/data.lmps
pair_style mliap unified {HERE}/MACE-OFF23_medium-mliap32_lammps.pt 0
pair_coeff * * C C C H
mass 1 12.010999996910238
mass 2 12.010999996910238
mass 3 12.010999996910238
mass 4 1.0079999997406976
neighbor        0.5 bin
neigh_modify    delay 50 every 2 check yes
thermo_style    custom step temp density vol press ke pe etotal spcpu
thermo_modify   flush yes
thermo          125
timestep        0.0005
fix fMOM all momentum 100 linear 1 1 1 angular
velocity all create 533.0 42 mom yes rot yes dist gaussian
"""


def stages() -> str:
    tdamp, pdamp = 100 * 0.0005, 1000 * 0.0005  # ps (metal)
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


if __name__ == "__main__":
    path = os.path.join(HERE, "in.tg4_maceoff_short")
    with open(path, "w") as f:
        f.write(HEADER + "\n" + stages() + "\n")
    print("wrote", path)
    print("melt", MELT_STEPS, "pre", PRE_STEPS, "run", RUN_STEPS,
          "total", MELT_STEPS + PRE_STEPS + 17 * RUN_STEPS)
