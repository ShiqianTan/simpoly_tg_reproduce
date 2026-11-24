import os
import subprocess

WORK = "/home/tione/notebook/home/tanshiqian/simpoly_tg_repro"
MC = os.path.join(WORK, "multi_pcff")
PY = "/home/tione/notebook/home/tanshiqian/envs/mace/bin/python"
PARSE = os.path.join(WORK, "parse_log.py")

JOBS = {
    "PS30": [
        ("tg_pcff_PS30.log", 42),
        ("tg_pcff_PS30s1.log", 1),
        ("tg_pcff_PS30s2.log", 2),
        ("tg_pcff_PS30s3.log", 3),
    ],
    "PMMA30": [
        ("tg_pcff_PMMA30.log", 42),
        ("tg_pcff_PMMA30s1.log", 1),
        ("tg_pcff_PMMA30s2.log", 2),
        ("tg_pcff_PMMA30s3.log", 3),
    ],
    "PMA30": [
        ("tg_pcff_PMA30.log", 42),
        ("tg_pcff_PMA30b.log", 7),
        ("tg_pcff_PMA30s1.log", 1),
        ("tg_pcff_PMA30s2.log", 2),
        ("tg_pcff_PMA30s3.log", 3),
    ],
    "PE30": [
        ("tg_pcff_PE30.log", 42),
        ("tg_pcff_PE30s1.log", 1),
        ("tg_pcff_PE30s2.log", 2),
        ("tg_pcff_PE30s3.log", 3),
    ],
}

header = None
for poly, items in JOBS.items():
    rows = []
    for log, seed in items:
        csv = os.path.join(MC, f"tmp_{poly}_{seed}.csv")
        subprocess.run(
            [PY, PARSE, "--log", os.path.join(MC, log), "--out", csv,
             "--model", "PCFF", "--poly-id", poly, "--seed", str(seed)],
            check=True, stdout=subprocess.DEVNULL,
        )
        with open(csv) as fh:
            lines = fh.read().strip().splitlines()
        if header is None:
            header = lines[0]
        rows.extend(lines[1:])
    out = os.path.join(MC, f"stages_pcff_{poly}_all.csv")
    with open(out, "w") as fh:
        fh.write(header + "\n" + "\n".join(rows) + "\n")
    print(f"wrote {out}: {len(rows)} rows ({len(items)} seeds)")
