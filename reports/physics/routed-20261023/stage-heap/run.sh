#!/bin/bash
# usage: run.sh lib side stage
lib=$1; side=$2; k=$3
sed "s/SIDE/$side/" stage$k.vi > d_${lib}_${side}_$k.vi
python3 ../../tools/vine_exec.py run --lib sph=$PWD/$lib --heap 12G d_${lib}_${side}_$k.vi > o_${lib}_${side}_$k.txt 2> e_${lib}_${side}_$k.txt
echo "$lib side=$side stage=$k heap=$(grep Heap e_${lib}_${side}_$k.txt | awk '{print $2}') W=$(grep -m1 Total e_${lib}_${side}_$k.txt | awk '{print $2}') $(tail -1 e_${lib}_${side}_$k.txt)"
