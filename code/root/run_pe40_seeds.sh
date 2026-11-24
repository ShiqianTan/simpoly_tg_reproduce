#!/bin/bash
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
PYEMC=/opt/conda/envs/simpoly/bin/python
PYMACE=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python

echo "########## BUILD PE40 PCFF seeds 1/2/3 ##########"
for s in 1 2 3; do
  L=PE40s$s
  $PYEMC multi_pcff/build_emc_poly.py PE 0.9 40 1944 $L $s > multi_pcff/build_$L.log 2>&1
  echo "build $L EXIT=$?"
  $PYMACE multi_pcff/make_input.py $L 433 113 20 0.5 20000 20 > multi_pcff/mk_$L.log 2>&1
  mv -f multi_pcff/in.tg_pcff_$L multi_pcff/in.tg_slow_$L
done

echo "########## RUNS (slow protocol) ##########"
GPU=2 bash run_env.sh multi_pcff/in.tg_slow_PE40s1 multi_pcff/tg_slow_PE40s1.log & P1=$!
GPU=3 bash run_env.sh multi_pcff/in.tg_slow_PE40s2 multi_pcff/tg_slow_PE40s2.log & P2=$!
wait $P1
GPU=2 bash run_env.sh multi_pcff/in.tg_slow_PE40s3 multi_pcff/tg_slow_PE40s3.log
echo "PE40_SEEDS_DONE"
