#!/bin/bash
# MACE-OFF23 SHORT-protocol cooling scans for PMMA30 and PMA30 (2 GPUs in parallel).
# melt 5000 @0.25fs + pre 5000 @0.5fs + 17 x 1250 stages, 533->213 K, dt 0.5 fs.
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro

GPU=2 bash run_mace_lammps.sh multi_pcff/in.tg_mace_PMMA30 multi_pcff/tg_mace_PMMA30.log &
P1=$!
GPU=3 bash run_mace_lammps.sh multi_pcff/in.tg_mace_PMA30 multi_pcff/tg_mace_PMA30.log &
P2=$!

wait $P1; echo "PMMA30 EXIT=$?"
wait $P2; echo "PMA30 EXIT=$?"
echo "MACE_PMPMA_DONE"
