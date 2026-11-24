#!/bin/bash
# STRICT-protocol PCFF cooling scans for n_ru=30 polymers (seed 42 cells).
# melt 20000 @ 0.5 fs -> pre 20000 -> 17 stages x 5000 (2.5 ps/stage) = 125000 steps.
# Sequential on GPU2 (override with GPU=<n> bash run_strict30.sh).
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
export GPU=${GPU:-2}
PY=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python
for spec in "PS30 533 213" "PMMA30 533 213" "PMA30 533 213" "PE30 433 113"; do
  set -- $spec
  P=$1; THI=$2; TLO=$3
  echo "########## STRICT $P ##########"
  $PY multi_pcff/make_input.py "$P" "$THI" "$TLO" 20 0.5 5000 10
  bash run_env.sh "multi_pcff/in.tg_pcff_$P" "multi_pcff/tg_strict_$P.log"
  echo "STRICT $P EXIT=$?"
done
echo "STRICT30 DONE"
