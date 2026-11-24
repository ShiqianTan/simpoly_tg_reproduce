#!/bin/bash
# Plan B: isothermal-equilibration scans.
# 50 ps held at each temperature (STAGE=100000 steps @0.5 fs) vs SLOW 10 ps,
# so each temperature is much closer to equilibrium. Records density AND pe.
# Writes NEW files: multi_pcff/in.tg_iso_<L>, multi_pcff/tg_iso_<L>.log
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
PY=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python

gen () {  # LABEL THI TLO MELT_DT GPU
  echo "### generating in.tg_iso_$1 (T $2 -> $3, melt_dt $4)"
  $PY multi_pcff/make_input.py "$1" "$2" "$3" 20 "$4" 100000 20
  mv -f "multi_pcff/in.tg_pcff_$1" "multi_pcff/in.tg_iso_$1"
  echo "########## ISO $1 on GPU $5 ##########"
  GPU=$5 bash run_env.sh "multi_pcff/in.tg_iso_$1" "multi_pcff/tg_iso_$1.log"
  echo "ISO $1 EXIT=$?"
}

gen PE30Lopls 433 113 0.5 0 &
gen PS30Lcmp  533 213 0.5 1 &
gen PE30L     433 113 0.5 2 &
gen PS30L     533 213 0.5 3 &
wait
echo ISO_DONE
