"""Generate SHORT-protocol cooling inputs for Vivace and PCFF that match
in.tg4_maceoff_short exactly (melt 5000 -> pre 5000 -> 17 x 1250, dt 0.5 fs).
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = "/home/tione/notebook/home/tanshiqian/simpoly_tg_repro"
DATA_METAL = f"{REPO}/small_emc/build/data.lmps"
DATA_FULL = f"{REPO}/small_emc/build/system.data"
PARAMS = f"{REPO}/small_emc/build/system.params"

TEMPS = [533, 513, 493, 473, 453, 433, 413, 393, 373, 353, 333, 313, 293, 273, 253, 233, 213]

METAL_HEADER = f"""# {{title}}
atom_style      atomic
atom_modify     map array sort 0 2.0
units           metal
newton          on
read_data       {DATA_METAL}
pair_style mliap unified {{model}} 0
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

PCFF_HEADER = f"""# {{title}}
atom_style      full
units           real
newton          on
read_data       {DATA_FULL}
kspace_style    pppm 1e-4
include         {PARAMS}
neighbor        1.5 bin
neigh_modify    delay 50 every 2 check yes
thermo_style    custom step temp density vol press ke pe etotal spcpu
thermo_modify   flush yes
thermo          125
timestep        0.5
fix fMOM all momentum 100 linear 1 1 1 angular
velocity all create 533.0 42 mom yes rot yes dist gaussian
"""


def protocol(tdamp, pdamp, melt_steps, stage_steps):
    lines = [
        "",
        "# Minimize",
        "min_style cg",
        "minimize 1e-4 1e-6 1000 10000",
        "",
        "# Melt at 700 K (NVT)",
        f"fix melt all nvt temp 700.0 700.0 {tdamp}",
        f"run {melt_steps}",
        "unfix melt",
        "",
        "# Pre-equilibration at 533 K (NPT)",
        f"fix pre all npt temp 533.0 533.0 {tdamp} aniso 1.000 1.000 {pdamp}",
        f"run {melt_steps}",
        "unfix pre",
        "",
    ]
    for i, t in enumerate(TEMPS):
        name = f"cool_{i:03d}_{t}K"
        lines += [
            f"# Stage: {name}",
            f"fix {name} all npt temp {t} {t} {tdamp} aniso 1.000 1.000 {pdamp}",
            f"run {stage_steps}",
            f"unfix {name}",
            "",
        ]
    return "\n".join(lines) + "\n"


def write(path, text):
    with open(path, "w") as fh:
        fh.write(text)
    print("wrote", path)


# Vivace (metal, tdamp 0.05 ps, pdamp 0.5 ps)
viv = METAL_HEADER.format(title="Vivace ML-IAP cooling scan v4 SHORT, 1944-atom EMC PS cell",
                          model="/checkpoints/cueq-0.8.mliap.pt")
write(f"{HERE}/in.tg4_vivace_short", viv + protocol(0.05, 0.5, 5000, 1250))

# PCFF (real, tdamp 50 fs, pdamp 500 fs)
pcff = PCFF_HEADER.format(title="PCFF cooling scan v4 SHORT, 1944-atom EMC PS cell")
write(f"{HERE}/in.tg4_pcff_short", pcff + protocol(50, 500, 5000, 1250))
