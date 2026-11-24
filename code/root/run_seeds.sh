#!/bin/bash
# Multi-seed PCFF cooling scans (n_ru=30) for statistics, on the free GPU2.
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
PY_EMC=/opt/conda/envs/simpoly/bin/python
PY=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python
export GPU=${GPU:-2}

run_one () {
  poly=$1; thi=$2; tlo=$3; seed=$4
  label=${poly}30s${seed}
  echo "=== build $label ==="
  $PY_EMC multi_pcff/build_emc_poly.py "$poly" 0.9 30 1944 "$label" "$seed" > "multi_pcff/build_$label.log" 2>&1
  $PY multi_pcff/make_input.py "$label" "$thi" "$tlo" 20 0.25
  echo "=== run $label ==="
  bash run_env.sh "multi_pcff/in.tg_pcff_$label" "multi_pcff/tg_pcff_$label.log"
  echo "$label EXIT=$?"
}

for seed in 1 2 3; do
  run_one PS   533 213 "$seed"
  run_one PMMA 533 213 "$seed"
  run_one PMA  533 213 "$seed"
  run_one PE   433 113 "$seed"
done
echo "SEEDS DONE"
