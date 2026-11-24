#!/bin/bash
# Sequential PCFF cooling scans for PMMA, PMA, PE (matched SHORT protocol).
# Uses GPU3 (override with GPU=<n> bash run_multi.sh).
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
export GPU=${GPU:-3}
for p in PMMA PMA PE; do
  echo "########## PCFF $p ##########"
  bash run_env.sh "multi_pcff/in.tg_pcff_$p" "multi_pcff/tg_pcff_$p.log"
  echo "PCFF $p EXIT=$?"
done
echo "MULTI PCFF DONE"
