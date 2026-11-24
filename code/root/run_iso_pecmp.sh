#!/bin/bash
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
PYEMC=/opt/conda/envs/simpoly/bin/python
PYMACE=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python

job () {
  local LABEL=$1 SEED=$2 GPU=$3
  echo "########## BUILD $LABEL (COMPASS, seed $SEED) ##########"
  $PYEMC multi_pcff/build_ff.py PE 0.9 30 8000 $LABEL $SEED compass > multi_pcff/build_$LABEL.log 2>&1
  echo "BUILD $LABEL EXIT=$?"
  $PYMACE multi_pcff/make_input.py $LABEL 433 113 20 0.5 100000 20 > multi_pcff/mk_$LABEL.log 2>&1
  mv -f multi_pcff/in.tg_pcff_$LABEL multi_pcff/in.tg_iso_$LABEL
  echo "########## ISO $LABEL on GPU $GPU ##########"
  GPU=$GPU bash run_env.sh multi_pcff/in.tg_iso_$LABEL multi_pcff/tg_iso_$LABEL.log
  echo "ISO $LABEL EXIT=$?"
}

job PE30Lcmp 42 0 &
job PE30Lcmpb 7 1 &
wait
echo "ISO_PEcmp_DONE"
