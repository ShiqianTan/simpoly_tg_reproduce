#!/bin/bash
# Run simpoly LAMMPS with the mace env's Python stack (e3nn 0.4.4, cueq 0.11.1, torch 2.8)
# so that MACE-OFF mliap pickles (converted in the mace env) can be loaded.
MACE_SP=/home/tione/notebook/home/tanshiqian/envs/mace/lib/python3.12/site-packages
SP=/opt/conda/envs/simpoly/lib/python3.12/site-packages
NV_LIBS=$(ls -d $MACE_SP/nvidia/*/lib 2>/dev/null | paste -sd:)
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/local/cuda-13.0/lib64:/usr/local/lammps/lib:$NV_LIBS:$SP/nvidia/cuda_nvrtc/lib
export PYTHONHOME=/opt/conda/envs/simpoly
export PYTHONPATH=$MACE_SP:$SP:/opt/conda/envs/simpoly/lib/python3.12
export PATH=/usr/local/lammps/bin:/opt/conda/envs/simpoly/bin:$PATH
export CUDA_VISIBLE_DEVICES=${GPU:-2}
export OMP_NUM_THREADS=4
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
/usr/local/lammps/bin/lmp -k on g 1 -sf kk -pk kokkos newton on neigh half \
  -in "$1" -log "$2" > "$2.out" 2>&1
echo "EXIT=$?" >> "$2.out"
