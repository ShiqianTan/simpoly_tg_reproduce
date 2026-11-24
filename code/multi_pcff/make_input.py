import os
import sys

POLY = sys.argv[1]
T_HIGH = float(sys.argv[2])
T_LOW = float(sys.argv[3])
T_STEP = float(sys.argv[4]) if len(sys.argv) > 4 else 20.0
MELT_DT = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
STAGE = int(sys.argv[6]) if len(sys.argv) > 6 else 1250
MELT_PS = float(sys.argv[7]) if len(sys.argv) > 7 else 2.5
COOL_DT = float(sys.argv[8]) if len(sys.argv) > 8 else 0.5
OUT_LABEL = sys.argv[9] if len(sys.argv) > 9 else POLY
MELT = int(round(MELT_PS * 1000.0 / MELT_DT))

WORK = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(WORK, POLY)
DATA = os.path.join(DIR, "system.data")
PARAMS = os.path.join(DIR, "system.params")
OUT = os.path.join(WORK, f"in.tg_pcff_{OUT_LABEL}")

temps = []
t = T_HIGH
while t >= T_LOW - 1e-6:
    temps.append(int(round(t)))
    t -= T_STEP

lines = [
    f"# PCFF cooling scan {POLY}, EMC cell (melt {MELT_PS}ps @ {MELT_DT}fs, {STAGE} steps/stage)",
    "atom_style      full",
    "units           real",
    "newton          on",
    f"read_data       {DATA}",
    "kspace_style    pppm 1e-4",
    f"include         {PARAMS}",
    "neighbor        1.5 bin",
    "neigh_modify    delay 50 every 2 check yes",
    "thermo_style    custom step temp density vol press ke pe etotal spcpu",
    "thermo_modify   flush yes",
    "thermo          125",
    "timestep        0.5",
    "fix fMOM all momentum 100 linear 1 1 1 angular",
    f"velocity all create {T_HIGH} 42 mom yes rot yes dist gaussian",
    "",
    "# Minimize",
    "min_style cg",
    "minimize 1e-4 1e-6 1000 10000",
    "",
    "# Melt at 700 K (NVT)",
    f"timestep        {MELT_DT}",
    "fix melt all nvt temp 700.0 700.0 50",
    f"run {MELT}",
    "unfix melt",
    f"timestep        {COOL_DT}",
    "",
    f"# Pre-equilibration at {T_HIGH} K (NPT)",
    f"fix pre all npt temp {T_HIGH} {T_HIGH} 50 aniso 1.000 1.000 500",
    f"run {MELT}",
    "unfix pre",
    "",
]
for i, T in enumerate(temps):
    name = f"cool_{i:03d}_{T}K"
    lines += [
        f"# Stage: {name}",
        f"fix {name} all npt temp {T} {T} 50 aniso 1.000 1.000 500",
        f"run {STAGE}",
        f"unfix {name}",
        "",
    ]

with open(OUT, "w") as fh:
    fh.write("\n".join(lines) + "\n")
print("wrote", OUT, "n_stages", len(temps), "temps", temps)
