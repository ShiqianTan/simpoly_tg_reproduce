#!/bin/bash
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/local/cuda-13.0/lib64:/usr/local/lammps/lib:/opt/conda/envs/simpoly/lib:/opt/conda/envs/simpoly/lib/python3.12/site-packages/nvidia/cuda_nvrtc/lib
export PYTHONHOME=/opt/conda/envs/simpoly
export PYTHONPATH=/home/tione/notebook/home/tanshiqian/github/polymer/tg/simpoly/src:/opt/conda/envs/simpoly/lib/python3.12/site-packages:/opt/conda/envs/simpoly/lib/python3.12
export PATH=/usr/local/lammps/bin:/opt/conda/envs/simpoly/bin:$PATH
export OMP_NUM_THREADS=4
export OMPI_ALLOW_RUN_AS_ROOT=1
export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro

echo "########## SINGLE GPU (1 rank) ##########"
CUDA_VISIBLE_DEVICES=1 mpirun -np 1 --bind-to none \
  /usr/local/lammps/bin/lmp -k on g 1 -sf kk -pk kokkos newton on neigh half \
  -in in.bench -log bench_g1.log > bench_g1.out 2>&1
echo "single EXIT=$?"

echo "########## FOUR GPUs (4 ranks) ##########"
CUDA_VISIBLE_DEVICES=0,1,2,3 mpirun -np 4 --bind-to none \
  /usr/local/lammps/bin/lmp -k on g 4 -sf kk -pk kokkos newton on neigh half \
  -in in.bench -log bench_g4.log > bench_g4.out 2>&1
echo "quad EXIT=$?"
echo "ALL DONE"
