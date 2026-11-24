#!/bin/bash
# Build longer-chain (n_ru=30) PCFF cells for PMMA, PMA, PS at density 0.9.
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro/multi_pcff
PY=/opt/conda/envs/simpoly/bin/python
echo "########## PMMA30 ##########"
$PY build_emc_poly.py PMMA 0.9 30 4000 PMMA30
echo "########## PMA30 ##########"
$PY build_emc_poly.py PMA 0.9 30 4000 PMA30
echo "########## PS30 ##########"
$PY build_emc_poly.py PS 0.9 30 4800 PS30
echo "BUILD ALL3 DONE"
