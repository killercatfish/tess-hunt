#!/bin/bash
tic=$1; secs=$2; per=$3
cd /tmp/tri && OMP_NUM_THREADS=2 nice -n 19 ionice -c3 timeout 14000 venv/bin/python -u triceratops_fpp.py --tic $tic --sectors $secs --period $per --fold /tmp/ecn/tri/${tic}_fold.csv --runs 4 --N 1000000 --out /tmp/ecn/tri/$tic > /tmp/ecn/tri/$tic.log 2>&1
echo "$tic exit $?" >> /tmp/ecn/tri/done.txt
