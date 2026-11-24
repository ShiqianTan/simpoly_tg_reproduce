#!/bin/bash
# Build a large (n_tot=8000) EMC cell for a given force field, generate the slow
# cooling input, and run it on the specified GPU.
# usage: bash run_ffL.sh POLY FIELD LABEL THI TLO MELT_DT GPU
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
SPY=/opt/conda/envs/simpoly/bin/python
MPY=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python

POLY=$1; FIELD=$2; LABEL=$3; THI=$4; TLO=$5; MDT=$6; GPUID=$7

echo "### build $LABEL ($POLY/$FIELD) on GPU$GPUID"
$SPY multi_pcff/build_ff.py "$POLY" 0.9 30 8000 "$LABEL" 42 "$FIELD" > "multi_pcff/build_$LABEL.log" 2>&1
$MPY multi_pcff/make_input.py "$LABEL" "$THI" "$TLO" 20 "$MDT" 20000 20 >> "multi_pcff/build_$LABEL.log" 2>&1
mv -f "multi_pcff/in.tg_pcff_$LABEL" "multi_pcff/in.tg_slow_$LABEL"
echo "BUILD_DONE $LABEL" >> "multi_pcff/build_$LABEL.log"

echo "### run $LABEL on GPU$GPUID"
GPU=$GPUID bash run_env.sh "multi_pcff/in.tg_slow_$LABEL" "multi_pcff/tg_slow_$LABEL.log" > "multi_pcff/run_$LABEL.out" 2>&1
echo "EXIT=$? $LABEL" >> "multi_pcff/run_$LABEL.out"
echo "FFL $LABEL DONE"
