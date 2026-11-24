#!/bin/bash
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
PYEMC=/opt/conda/envs/simpoly/bin/python
PYMACE=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python

echo "########## BUILD PE40b (PE n_ru=40, seed 7, PCFF) ##########"
$PYEMC multi_pcff/build_emc_poly.py PE 0.9 40 1944 PE40b 7 > multi_pcff/build_PE40b.log 2>&1
echo "build PE40b EXIT=$?"
$PYMACE multi_pcff/make_input.py PE40b 433 113 20 0.5 20000 20 > multi_pcff/mk_PE40b.log 2>&1
mv -f multi_pcff/in.tg_pcff_PE40b multi_pcff/in.tg_slow_PE40b

echo "########## WAIT for PE40opls (PID 3085887) to free GPU2 ##########"
while kill -0 3085887 2>/dev/null; do sleep 20; done
sleep 10
echo "########## RUN PE40b (slow protocol) on GPU2 ##########"
GPU=2 bash run_env.sh multi_pcff/in.tg_slow_PE40b multi_pcff/tg_slow_PE40b.log
echo "PE40b EXIT=$?"
echo "PE40b_DONE"
