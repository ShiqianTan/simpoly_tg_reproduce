#!/bin/bash
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
PYEMC=/opt/conda/envs/simpoly/bin/python
PYMACE=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python

echo "########## BUILD PMA30 OPLS seeds 1/2/3 ##########"
for s in 1 2 3; do
  L=PMA30opls_s$s
  $PYEMC multi_pcff/build_ff.py PMA 0.9 30 1944 $L $s opls > multi_pcff/build_$L.log 2>&1
  echo "build $L EXIT=$?"
  $PYMACE multi_pcff/make_input.py $L 533 213 20 0.25 20000 20 > multi_pcff/mk_$L.log 2>&1
  mv -f multi_pcff/in.tg_pcff_$L multi_pcff/in.tg_slow_$L
done

echo "########## RUNS (slow protocol) ##########"
GPU=2 bash run_env.sh multi_pcff/in.tg_slow_PMA30opls_s1 multi_pcff/tg_slow_PMA30opls_s1.log & P1=$!
GPU=3 bash run_env.sh multi_pcff/in.tg_slow_PMA30opls_s2 multi_pcff/tg_slow_PMA30opls_s2.log & P2=$!
wait $P1
GPU=2 bash run_env.sh multi_pcff/in.tg_slow_PMA30opls_s3 multi_pcff/tg_slow_PMA30opls_s3.log
echo "PMA_OPLS_SEEDS_DONE"
