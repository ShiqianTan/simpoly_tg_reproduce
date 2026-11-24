import sys
sys.path.append("/opt/conda/envs/simpoly/lib/python3.12/site-packages")

from mattersim.lammps.mliap_wrapper import MatterSimMLIAP

mliap = MatterSimMLIAP.from_checkpoint("mattersim-v1.0.0-1M", device="cpu", compile=False)
mliap.save("/home/tione/notebook/home/tanshiqian/simpoly_tg_repro/compare1944/mattersim-v1.0.0-1M_mliap.pt")
print("SAVED mattersim mliap model")
