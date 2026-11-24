#!/bin/bash
# Build ~8000-atom (n_tot=8000) n_ru=30 cells for PS/PMMA/PE at density 0.9, then
# generate SLOW-protocol cooling inputs (10 ps/stage, melt 20 ps + pre 20 ps).
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
SPY=/opt/conda/envs/simpoly/bin/python
MPY=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python

build () {  # POLY LABEL
  echo "### building $2"
  $SPY multi_pcff/build_emc_poly.py "$1" 0.9 30 8000 "$2" 42
}

gen () {  # LABEL THI TLO MELT_DT
  echo "### input $1 (T $2 -> $3, melt_dt $4)"
  $MPY multi_pcff/make_input.py "$1" "$2" "$3" 20 "$4" 20000 20
  mv -f "multi_pcff/in.tg_pcff_$1" "multi_pcff/in.tg_slow_$1"
}

build PS   PS30L
gen   PS30L   533 213 0.5
build PMMA PMMA30L
gen   PMMA30L 533 213 0.25
build PE   PE30L
gen   PE30L   433 113 0.5
echo "LARGE_BUILD_DONE"
