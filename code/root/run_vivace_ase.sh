#!/bin/bash
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/local/cuda-13.0/lib64:/usr/local/lammps/lib:/opt/conda/envs/simpoly/lib:/opt/conda/envs/simpoly/lib/python3.12/site-packages/nvidia/cuda_nvrtc/lib
export PYTHONHOME=/opt/conda/envs/simpoly
export PYTHONPATH=/home/tione/notebook/home/tanshiqian/github/polymer/tg/simpoly/src:/opt/conda/envs/simpoly/lib/python3.12/site-packages:/opt/conda/envs/simpoly/lib/python3.12
export CUDA_VISIBLE_DEVICES=${GPU:-3}
export OMP_NUM_THREADS=4
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
/opt/conda/envs/simpoly/bin/python compare1944/ase_cooling_vivace.py --tag vivace_ase > compare1944/tg_vivace_ase.out 2>&1
echo EXIT=$? >> compare1944/tg_vivace_ase.out
