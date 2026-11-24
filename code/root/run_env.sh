#!/bin/bash
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/local/cuda-13.0/lib64:/usr/local/lammps/lib:/opt/conda/envs/simpoly/lib:/opt/conda/envs/simpoly/lib/python3.12/site-packages/nvidia/cuda_nvrtc/lib
export PYTHONHOME=/opt/conda/envs/simpoly
export PYTHONPATH=/home/tione/notebook/home/tanshiqian/github/polymer/tg/simpoly/src:/opt/conda/envs/simpoly/lib/python3.12/site-packages:/opt/conda/envs/simpoly/lib/python3.12
export PATH=/usr/local/lammps/bin:/opt/conda/envs/simpoly/bin:$PATH
export CUDA_VISIBLE_DEVICES=${GPU:-3}
export OMP_NUM_THREADS=4
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
/usr/local/lammps/bin/lmp -k on g 1 -sf kk -pk kokkos newton on neigh half \
  -in "$1" -log "$2" > "$2.out" 2>&1
echo "EXIT=$?" >> "$2.out"
