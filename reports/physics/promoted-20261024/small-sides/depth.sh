#!/bin/bash
lib=$1; side=$2; k=$3
sed "s/SIDE/$side/" stage$k.vi > dd_${lib}_${side}_$k.vi
python3 ../../tools/vine_exec.py run --depth --lib sph=$PWD/$lib --heap 12G dd_${lib}_${side}_$k.vi > do_${lib}_${side}_$k.txt 2> de_${lib}_${side}_$k.txt
echo "$lib side=$side stage=$k depth=$(grep Depth de_${lib}_${side}_$k.txt | awk '{print $2}') heap=$(grep Heap de_${lib}_${side}_$k.txt | awk '{print $2}') W=$(grep -m1 Total de_${lib}_${side}_$k.txt | awk '{print $2}') out=$(cat do_${lib}_${side}_$k.txt)"
