#!/bin/bash
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
PY=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python

echo "########## GENERATE MACE-OFF23 SHORT inputs (PE30 seed42, PE30b seed7) ##########"
$PY multi_pcff/make_input_mace.py PE30  433 113 20 0.5 1250 2.5
$PY multi_pcff/make_input_mace.py PE30b 433 113 20 0.5 1250 2.5

echo "########## RUN MACE (GPU2: PE30, GPU3: PE30b) ##########"
GPU=2 bash run_mace_lammps.sh multi_pcff/in.tg_mace_PE30  multi_pcff/tg_mace_PE30.log  & P1=$!
GPU=3 bash run_mace_lammps.sh multi_pcff/in.tg_mace_PE30b multi_pcff/tg_mace_PE30b.log & P2=$!
wait $P1 $P2
echo "MACE_PE_DONE"
