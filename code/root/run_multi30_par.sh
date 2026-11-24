#!/bin/bash
# Parallel PCFF cooling scans for the longer-chain (n_ru=30) cells: one polymer per GPU.
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
GPU=0 bash run_env.sh multi_pcff/in.tg_pcff_PMMA30 multi_pcff/tg_pcff_PMMA30.log &
GPU=1 bash run_env.sh multi_pcff/in.tg_pcff_PMA30  multi_pcff/tg_pcff_PMA30.log  &
GPU=2 bash run_env.sh multi_pcff/in.tg_pcff_PS30   multi_pcff/tg_pcff_PS30.log   &
wait
echo "MULTI30 PCFF PARALLEL DONE"
