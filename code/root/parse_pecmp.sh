#!/bin/bash
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
PY=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python
REPO=/home/tione/notebook/home/tanshiqian/github/polymer/tg/simpoly

echo "waiting for PE30Lcmp / PE30Lcmpb ..."
while kill -0 3066694 2>/dev/null || kill -0 3066722 2>/dev/null; do sleep 20; done
sleep 15

for L in PE30Lcmp PE30Lcmpb; do
  $PY parse_iso.py --log multi_pcff/tg_iso_$L.log --out multi_pcff/stages_iso_$L.csv > multi_pcff/parse_iso_$L.out 2>&1
  $PY iso_to_stages.py multi_pcff/stages_iso_$L.csv multi_pcff/iso_${L}_stages.csv COMPASS $L 42 >/dev/null 2>&1
  $PY iso_to_stages.py multi_pcff/stages_iso_$L.csv multi_pcff/isoE_${L}_stages.csv COMPASS $L 42 pe >/dev/null 2>&1
  echo "===== $L ====="
  echo -n "rho-Tg: "; $PY bilinear_cont_tg.py multi_pcff/iso_${L}_stages.csv 2>/dev/null | tail -1
  echo -n "E-Tg:   "; $PY bilinear_cont_tg.py multi_pcff/isoE_${L}_stages.csv 2>/dev/null | tail -1
done
echo "ISO_PECMP_PARSE_DONE"
