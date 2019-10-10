#!/bin/bash

# Initialise
#=====================================================

solstice_dir='/home/yewang/Solstice-0.8.1-GNU-Linux64'

#======================================================
#
#
#
python set_case.py
#
case_dir="`cat $solstice_dir/casedir.input`"
azimuth="`cat $case_dir/azimuth.input`"
elevation="`cat $case_dir/elevation.input`"
num_rays="`cat $case_dir/rays.input`"
rho_mirror="`cat $case_dir/mirror.input`"

solstice_pack=$solstice_dir'/etc/solstice.profile'
source $solstice_pack
# run solstice
#
solstice -D$azimuth,$elevation -v -n $num_rays -R $case_dir/input-rcv.yaml -fo $case_dir/simul $case_dir/input.yaml
#
# preparing post processing
solstice -D$azimuth,$elevation -g format=obj:split=geometry -fo $case_dir/geom $case_dir/input.yaml
solstice -D$azimuth,$elevation -q -n 100 -R $case_dir/input-rcv.yaml -p default $case_dir/input.yaml > $case_dir/solpaths
#
# postprocessing in C (provided by Cyril Caliot)
#Read "simul" results and produce a text file with the raw results
gcc $solstice_dir/src-Linux/ppLinux/solppraw.c -o $solstice_dir/src-Linux/ppLinux/solppraw
$solstice_dir/src-Linux/ppLinux/solppraw $case_dir/simul
#Read "simul" results and produce receiver files (.vtk) of incoming and/or absorbed solar flux per-primitive
gcc $solstice_dir/src-Linux/ppLinux/solmaps.c -o $solstice_dir/src-Linux/ppLinux/solmaps
$solstice_dir/src-Linux/ppLinux/solmaps $case_dir/simul

#Read "geom" and "simul" file results and produce primaries and receivers files (.vtk), and .obj geometry files
gcc $solstice_dir/src-Linux/ppLinux/solpp.c -o $solstice_dir/src-Linux/ppLinux/solpp
$solstice_dir/src-Linux/ppLinux/solpp $case_dir/geom $case_dir/simul

#Read "solpaths" file and produce readable file (.vtk) by paraview to visualize the ray paths
gcc $solstice_dir/src-Linux/ppLinux/solpaths.c -o $solstice_dir/src-Linux/ppLinux/solpath
$solstice_dir/src-Linux/ppLinux/solpath $case_dir/solpaths

mv *vtk $case_dir
mv *obj $case_dir
mv *txt $case_dir
rm $solstice_dir/*.input
rm $case_dir/*input


rawfile=$case_dir'/simul'
python $solstice_dir/src-Linux/srcPy/get_raw.py $rawfile $case_dir $rho_mirror
