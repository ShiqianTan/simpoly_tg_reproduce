#!/bin/bash
# Resilient dispatcher: runs each label on the first GPU that has >=60 GB free.
# MACE mliap needs ~65 GB, so one job per GPU and only on an idle card.
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro

LOCKDIR=/tmp/opencode/mace_gpu_locks
mkdir -p "$LOCKDIR"

try_gpu() {
  local G free
  for G in 0 1 2 3; do
    if mkdir "$LOCKDIR/gpu$G" 2>/dev/null; then
      free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i "$G" 2>/dev/null)
      if [ -n "$free" ] && [ "$free" -gt 60000 ]; then
        echo "$G"
        return 0
      fi
      rmdir "$LOCKDIR/gpu$G"
    fi
  done
  return 1
}

run_one() {
  local L=$1
  while true; do
    local G
    G=$(try_gpu)
    if [ -n "$G" ]; then
      echo "LAUNCH $L on GPU$G $(date +%H:%M:%S)"
      GPU=$G bash run_mace_lammps.sh "multi_pcff/in.tg_mace_iso_$L" "multi_pcff/tg_mace_iso_$L.log"
      rmdir "$LOCKDIR/gpu$G"
      if grep -q 'Total wall time' "multi_pcff/tg_mace_iso_$L.log" 2>/dev/null; then
        echo "OK $L on GPU$G $(date +%H:%M:%S)"
        return 0
      fi
      echo "RETRY $L (run failed) $(date +%H:%M:%S)"
    fi
    sleep 60
  done
}

for L in "$@"; do run_one "$L" & done
wait
echo "MACE_ISO_RETRY_DONE $(date +%H:%M:%S)"
