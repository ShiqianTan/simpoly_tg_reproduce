#!/bin/bash
# SLOW-protocol PCFF cooling scans for the four n_ru=30 seed-42 cells.
# 10 ps per cooling stage (20000 steps @0.5 fs) vs STRICT 2.5 ps and SHORT 0.625 ps.
# Writes NEW files (in.tg_slow_<P>, tg_slow_<P>.log) so old data is not overwritten.
# Uses GPU2 by default (override with GPU=<n> bash run_slow30.sh).
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
export GPU=${GPU:-2}
PY=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python

gen () {  # POLY THI TLO MELT_DT
  echo "### generating in.tg_slow_$1 (T $2 -> $3, melt_dt $4, 20000 steps/stage)"
  $PY multi_pcff/make_input.py "$1" "$2" "$3" 20 "$4" 20000 20
  mv -f "multi_pcff/in.tg_pcff_$1" "multi_pcff/in.tg_slow_$1"
}

run () {  # POLY
  echo "########## SLOW $1 ##########"
  bash run_env.sh "multi_pcff/in.tg_slow_$1" "multi_pcff/tg_slow_$1.log"
  echo "SLOW $1 EXIT=$?"
}

gen PS30   533 213 0.5
gen PMMA30 533 213 0.25
gen PMA30  533 213 0.25
gen PE30   433 113 0.5

run PS30
run PMMA30
run PMA30
run PE30
echo "SLOW30 DONE"
