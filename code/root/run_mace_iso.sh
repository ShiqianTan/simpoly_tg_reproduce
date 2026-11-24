#!/bin/bash
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro

run() {
  local G=$1 L=$2
  echo "START $L on GPU$G $(date +%H:%M:%S)"
  GPU=$G bash run_mace_lammps.sh multi_pcff/in.tg_mace_iso_$L multi_pcff/tg_mace_iso_$L.log
  echo "DONE $L EXIT=$? $(date +%H:%M:%S)"
}

run 0 PMMA30  &
P1=$!
run 2 PMMA30b &
P2=$!
run 3 PMA30   &
P3=$!

while kill -0 $P1 2>/dev/null && kill -0 $P2 2>/dev/null && kill -0 $P3 2>/dev/null; do
  sleep 60
done

if ! kill -0 $P1 2>/dev/null; then G=0
elif ! kill -0 $P2 2>/dev/null; then G=2
else G=3
fi
run $G PMA30b

wait
echo MACE_ISO_DONE $(date +%H:%M:%S)
