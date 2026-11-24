#!/bin/bash
# Wait for the MACE PMMA30/PMA30 lmp processes, then parse logs into stages CSVs and fit Tg.
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
PY=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python
REPO=/home/tione/notebook/home/tanshiqian/github/polymer/tg/simpoly

for PID in "$@"; do
  while kill -0 "$PID" 2>/dev/null; do sleep 60; done
done
echo "MACE_PMPMA lmp finished"

for L in PMMA30 PMA30; do
  $PY parse_log.py --log multi_pcff/tg_mace_$L.log --out multi_pcff/stages_mace_$L.csv --model MACE-OFF --poly-id $L
done

for L in PMMA30 PMA30; do
  PYTHONPATH=$REPO/src $PY $REPO/src/simpoly/poly_arena/analysis/cli/cooling_protocol.py \
    --inputs multi_pcff/stages_mace_$L.csv --out multi_pcff/tg_mace_fit_$L
  echo "--- bilinear $L ---"
  $PY bilinear_cont_tg.py multi_pcff/stages_mace_$L.csv
done
echo "MACE_PMPMA_POST_DONE"
