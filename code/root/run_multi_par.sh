#!/bin/bash
# Parallel PCFF cooling scans: one polymer per GPU.
# PMMA -> GPU2 (free), PMA -> GPU3, PE -> GPU0.
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
GPU=2 bash run_env.sh multi_pcff/in.tg_pcff_PMMA multi_pcff/tg_pcff_PMMA.log &
GPU=3 bash run_env.sh multi_pcff/in.tg_pcff_PMA  multi_pcff/tg_pcff_PMA.log  &
GPU=0 bash run_env.sh multi_pcff/in.tg_pcff_PE   multi_pcff/tg_pcff_PE.log   &
wait
echo "MULTI PCFF PARALLEL DONE"
