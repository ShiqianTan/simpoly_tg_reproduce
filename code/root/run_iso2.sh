#!/bin/bash
# Plan B extension: isothermal-equilibration scans for PMMA / PMA (PCFF + OPLS).
# Same protocol as run_iso.sh: 50 ps held at each temperature (STAGE=100000 @0.5 fs),
# melt 20 ps + pre-equilibration, 17 NPT-aniso stages 533 -> 213 K.
# Writes NEW files: multi_pcff/in.tg_iso_<L>, multi_pcff/tg_iso_<L>.log
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
PY=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python

# wait for the EMC builds to finish (PMA30L + PMMA30Lopls)
echo "waiting for builds..."
while [ ! -f multi_pcff/PMA30L/system.data ] || [ ! -f multi_pcff/PMMA30Lopls/system.data ]; do
  sleep 20
done
sleep 5
echo "builds present"

gen () {  # LABEL THI TLO MELT_DT GPU
  echo "### generating in.tg_iso_$1 (T $2 -> $3, melt_dt $4)"
  $PY multi_pcff/make_input.py "$1" "$2" "$3" 20 "$4" 100000 20
  mv -f "multi_pcff/in.tg_pcff_$1" "multi_pcff/in.tg_iso_$1"
  echo "########## ISO $1 on GPU $5 ##########"
  GPU=$5 bash run_env.sh "multi_pcff/in.tg_iso_$1" "multi_pcff/tg_iso_$1.log"
  echo "ISO $1 EXIT=$?"
}

gen PMMA30L     533 213 0.25 0 &
gen PMA30L      533 213 0.25 1 &
gen PMMA30Lopls 533 213 0.25 2 &
gen PMA30Lopls  533 213 0.25 3 &
wait
echo ISO2_DONE
