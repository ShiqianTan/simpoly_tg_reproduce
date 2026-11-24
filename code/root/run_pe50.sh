#!/bin/bash
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
PYEMC=/opt/conda/envs/simpoly/bin/python
PYMACE=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python

echo "########## BUILD PE n_ru=50 (PCFF) ##########"
$PYEMC multi_pcff/build_emc_poly.py PE 0.9 50 1944 PE50 42 > multi_pcff/build_PE50.log 2>&1
echo "build PE50 EXIT=$?"
$PYMACE multi_pcff/make_input.py PE50 433 113 20 0.5 20000 20 > multi_pcff/mk_PE50.log 2>&1
mv -f multi_pcff/in.tg_pcff_PE50 multi_pcff/in.tg_slow_PE50

echo "########## RUN PE50 (slow protocol) ##########"
GPU=3 bash run_env.sh multi_pcff/in.tg_slow_PE50 multi_pcff/tg_slow_PE50.log
echo "PE50 EXIT=$?"
echo "PE50_DONE"
