#!/bin/bash
# Sequential SHORT-protocol cooling scans for Vivace and PCFF (matched to MACE-OFF short).
# Uses GPU3 (override with GPU=<n> bash run_short.sh).
cd /home/tione/notebook/home/tanshiqian/simpoly_tg_repro
export GPU=${GPU:-3}
echo "########## VIVACE SHORT ##########"
bash run_env.sh compare1944/in.tg4_vivace_short compare1944/tg4_vivace_short.log
echo "VIVACE EXIT=$?"
echo "########## PCFF SHORT ##########"
bash run_env.sh compare1944/in.tg4_pcff_short compare1944/tg4_pcff_short.log
echo "PCFF EXIT=$?"
echo "SHORT RUNS DONE"
