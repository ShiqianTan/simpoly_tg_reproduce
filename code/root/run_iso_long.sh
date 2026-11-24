#!/bin/bash
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
PY=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python

echo "########## GENERATE long-hold isothermal inputs (same PE30L cell) ##########"
$PY multi_pcff/make_input.py PE30L 433 113 20 0.5 200000 20 0.5 PE30L_h100
$PY multi_pcff/make_input.py PE30L 433 113 20 0.5 400000 20 0.5 PE30L_h200
mv -f multi_pcff/in.tg_pcff_PE30L_h100 multi_pcff/in.tg_iso_PE30L_h100
mv -f multi_pcff/in.tg_pcff_PE30L_h200 multi_pcff/in.tg_iso_PE30L_h200

echo "########## RUN 100 ps/stage (GPU0) + 200 ps/stage (GPU1) ##########"
GPU=0 bash run_env.sh multi_pcff/in.tg_iso_PE30L_h100 multi_pcff/tg_iso_PE30L_h100.log & P1=$!
GPU=1 bash run_env.sh multi_pcff/in.tg_iso_PE30L_h200 multi_pcff/tg_iso_PE30L_h200.log & P2=$!
wait $P1 $P2
echo "ISO_LONG_DONE"
