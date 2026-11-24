#!/bin/bash
# Wait for a MatterSim LAMMPS run to finish, then parse + fit Tg.
# Usage: bash run_ms_post.sh <lmp_pid> <LABEL>
PY=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python
REPO=/home/tione/notebook/home/tanshiqian/github/polymer/tg/simpoly
WORK=/home/tione/notebook/home/tanshiqian/simpoly_tg_repro
cd "$WORK"

PID="$1"
LABEL="$2"
while kill -0 "$PID" 2>/dev/null; do sleep 60; done
echo "MatterSim run $LABEL finished"

$PY parse_log.py --log multi_pcff/tg_ms_${LABEL}.log --out multi_pcff/stages_ms_${LABEL}.csv --model MatterSim --poly-id "$LABEL"
PYTHONPATH=$REPO/src $PY $REPO/src/simpoly/poly_arena/analysis/cli/cooling_protocol.py \
  --inputs multi_pcff/stages_ms_${LABEL}.csv --out multi_pcff/tg_ms_fit_${LABEL}
$PY bilinear_cont_tg.py multi_pcff/stages_ms_${LABEL}.csv
$PY hyperbolic_tg.py multi_pcff/stages_ms_${LABEL}.csv
echo "MS_POST_DONE $LABEL"
