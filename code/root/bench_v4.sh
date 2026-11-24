#!/bin/bash
# Sequential NVE ns/day benchmark of the three models on the 1944-atom PS cell.
# Uses GPU3 (override with GPU=<n> bash bench_v4.sh).
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
export GPU=${GPU:-3}
echo "########## VIVACE (mliap) ##########"
bash run_env.sh compare1944/in.bench_v4_vivace compare1944/bench_v4_vivace.log
grep -E "Loop time|Performance" compare1944/bench_v4_vivace.log
echo "########## PCFF ##########"
bash run_env.sh compare1944/in.bench_v4_pcff compare1944/bench_v4_pcff.log
grep -E "Loop time|Performance" compare1944/bench_v4_pcff.log
echo "########## MACE-OFF23 medium (mliap f32) ##########"
bash run_mace_lammps.sh compare1944/in.bench_v4_maceoff compare1944/bench_v4_maceoff.log
grep -E "Loop time|Performance" compare1944/bench_v4_maceoff.log
echo "ALL BENCH DONE"
