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
DATA = os.path.join(DIR, "data.lmps")
MODEL = os.path.join(os.path.dirname(WORK), "compare1944", "mattersim-v1.0.0-1M_mliap.pt")
OUT = os.path.join(WORK, f"in.tg_ms_{OUT_LABEL}")


def read_types(poly_dir):
    sysdata = os.path.join(poly_dir, "system.data")
    out = []
    in_m = False
    with open(sysdata) as fh:
        for ln in fh:
            s = ln.strip()
            if s.startswith("Masses"):
                in_m = True
                continue
            if not in_m:
                continue
            if not s:
                continue
            if s[0].isalpha():
                break
            parts = s.split("#")
            nums = parts[0].split()
            label = parts[1].strip() if len(parts) > 1 else ""
            out.append((int(nums[0]), float(nums[1]), label))
    if not out:
        raise RuntimeError(f"no Masses section found in {sysdata}")
    return out


def elem_from_label(label):
    l = label.lower()
    for pre, el in (("cl", "Cl"), ("c", "C"), ("h", "H"), ("o", "O"),
                    ("n", "N"), ("f", "F"), ("s", "S"), ("p", "P"), ("br", "Br")):
        if l.startswith(pre):
            return el
    raise RuntimeError(f"cannot map element label {label!r}")


types = read_types(DIR)
elems = [elem_from_label(lbl) for _, _, lbl in types]
pair_coeff = " ".join(elems)
mass_lines = [f"mass {t} {m}" for t, m, _ in types]

temps = []
t = T_HIGH
while t >= T_LOW - 1e-6:
    temps.append(int(round(t)))
    t -= T_STEP

lines = [
    f"# MatterSim v1.0.0-1M cooling scan {POLY}, EMC cell (melt {MELT_PS}ps @ {MELT_DT}fs, {STAGE} steps/stage)",
    "atom_style      atomic",
    "atom_modify     map array sort 0 2.0",
    "units           metal",
    "newton          on",
    f"read_data       {DATA}",
    f"pair_style      mliap unified {MODEL}",
    f"pair_coeff      * * {pair_coeff}",
    *mass_lines,
    "neighbor        0.5 bin",
    "neigh_modify    delay 50 every 2 check yes",
    "thermo_style    custom step temp density vol press ke pe etotal spcpu",
    "thermo_modify   flush yes",
    "thermo          125",
    "timestep        0.0005",
    "fix fMOM all momentum 100 linear 1 1 1 angular",
    f"velocity all create {T_HIGH} 42 mom yes rot yes dist gaussian",
    "",
    "# Minimize",
    "min_style cg",
    "minimize 1e-4 1e-6 1000 10000",
    "",
    "# Melt at 700 K (NVT)",
    f"timestep        {MELT_DT/1000.0}",
    "fix melt all nvt temp 700.0 700.0 0.05",
    f"run {MELT}",
    "unfix melt",
    f"timestep        {COOL_DT/1000.0}",
    "",
    f"# Pre-equilibration at {T_HIGH} K (NPT)",
    f"fix pre all npt temp {T_HIGH} {T_HIGH} 0.05 aniso 1.000 1.000 0.5",
    f"run {MELT}",
    "unfix pre",
    "",
]
for i, T in enumerate(temps):
    name = f"cool_{i:03d}_{T}K"
    lines += [
        f"# Stage: {name}",
        f"fix {name} all npt temp {T} {T} 0.05 aniso 1.000 1.000 0.5",
        f"run {STAGE}",
        f"unfix {name}",
        "",
    ]

with open(OUT, "w") as fh:
    fh.write("\n".join(lines) + "\n")
print("wrote", OUT, "n_stages", len(temps), "temps", temps)
print("elements", elems)
print("masses", mass_lines)
