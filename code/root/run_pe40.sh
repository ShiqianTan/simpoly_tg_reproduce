#!/bin/bash
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
PYEMC=/opt/conda/envs/simpoly/bin/python
PYMACE=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python

echo "########## BUILDS (PE n_ru=40, density 0.9) ##########"
$PYEMC multi_pcff/build_emc_poly.py PE 0.9 40 1944 PE40 42      > multi_pcff/build_PE40.log 2>&1
echo "build PE40     EXIT=$?"
$PYEMC multi_pcff/build_ff.py      PE 0.9 40 1944 PE40cmp 42 compass > multi_pcff/build_PE40cmp.log 2>&1
echo "build PE40cmp  EXIT=$?"
$PYEMC multi_pcff/build_ff.py      PE 0.9 40 1944 PE40opls 42 opls   > multi_pcff/build_PE40opls.log 2>&1
echo "build PE40opls EXIT=$?"

for L in PE40 PE40cmp PE40opls; do
  $PYMACE multi_pcff/make_input.py $L 433 113 20 0.5 20000 20 > multi_pcff/mk_$L.log 2>&1
  mv -f multi_pcff/in.tg_pcff_$L multi_pcff/in.tg_slow_$L
  echo "input $L ready"
done

echo "########## RUNS (slow protocol, 10 ps/stage) ##########"
GPU=2 bash run_env.sh multi_pcff/in.tg_slow_PE40     multi_pcff/tg_slow_PE40.log &
P1=$!
GPU=3 bash run_env.sh multi_pcff/in.tg_slow_PE40cmp  multi_pcff/tg_slow_PE40cmp.log &
P2=$!
wait $P1; echo "PE40     EXIT=$?"
wait $P2; echo "PE40cmp  EXIT=$?"
GPU=2 bash run_env.sh multi_pcff/in.tg_slow_PE40opls multi_pcff/tg_slow_PE40opls.log
echo "PE40opls EXIT=$?"
echo "PE40_DONE"
