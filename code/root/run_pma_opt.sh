#!/bin/bash
# PMA cell/equilibration optimization experiments, 4 GPUs in parallel.
# All use the SLOW cooling protocol (10 ps/stage); one factor changed per GPU.
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
PYM=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python
PYS=/opt/conda/envs/simpoly/bin/python

echo "=== builds ==="
$PYS multi_pcff/build_emc_poly.py PMA 0.6 30 4000 PMAoptA 42 > multi_pcff/build_PMAoptA.log 2>&1
$PYS multi_pcff/build_emc_poly.py PMA 0.9 30 4000 PMAoptB 42 > multi_pcff/build_PMAoptB.log 2>&1
$PYS multi_pcff/build_emc_poly.py PMA 0.9 30 8000 PMAoptC 42 > multi_pcff/build_PMAoptC.log 2>&1
$PYS multi_pcff/build_emc_poly.py PMA 0.9 30 4000 PMAoptD 11 > multi_pcff/build_PMAoptD.log 2>&1

echo "=== inputs ==="
$PYM multi_pcff/make_input.py PMAoptA 533 213 20 0.25 20000 100
$PYM multi_pcff/make_input.py PMAoptB 533 213 20 0.25 20000 100
$PYM multi_pcff/make_input.py PMAoptC 533 213 20 0.25 20000 20
$PYM multi_pcff/make_input.py PMAoptD 533 213 20 0.25 20000 20

echo "=== launching 4 parallel runs ==="
GPU=0 bash run_env.sh multi_pcff/in.tg_pcff_PMAoptA multi_pcff/tg_opt_PMAoptA.log > multi_pcff/run_optA.out 2>&1 &
GPU=2 bash run_env.sh multi_pcff/in.tg_pcff_PMAoptB multi_pcff/tg_opt_PMAoptB.log > multi_pcff/run_optB.out 2>&1 &
GPU=3 bash run_env.sh multi_pcff/in.tg_pcff_PMAoptC multi_pcff/tg_opt_PMAoptC.log > multi_pcff/run_optC.out 2>&1 &
GPU=1 bash run_env.sh multi_pcff/in.tg_pcff_PMAoptD multi_pcff/tg_opt_PMAoptD.log > multi_pcff/run_optD.out 2>&1 &
wait
echo "PMA_OPT_DONE"
