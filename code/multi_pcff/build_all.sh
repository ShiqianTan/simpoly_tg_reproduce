#!/bin/bash
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro/multi_pcff
PY=/opt/conda/envs/simpoly/bin/python
for p in PMMA PMA PE; do
  echo "########## BUILD $p ##########"
  $PY build_emc_poly.py $p
  echo "BUILD $p EXIT=$?"
done
echo "BUILD ALL DONE"
