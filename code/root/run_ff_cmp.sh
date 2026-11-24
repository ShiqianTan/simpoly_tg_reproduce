#!/bin/bash
# Sequential slow-protocol cooling scans for a list of labels on one GPU.
# Usage: GPU=<n> bash run_ff_cmp.sh <LABEL> [<LABEL> ...]
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
export GPU=${GPU:-2}
for P in "$@"; do
  echo "########## FF $P (GPU $GPU) ##########"
  bash run_env.sh "multi_pcff/in.tg_slow_$P" "multi_pcff/tg_slow_$P.log"
  echo "FF $P EXIT=$?"
done
echo "FF_CMP_GPU${GPU} DONE"
