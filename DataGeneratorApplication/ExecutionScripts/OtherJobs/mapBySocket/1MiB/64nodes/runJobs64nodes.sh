#!/bin/bash -l

#SBATCH --job-name=runFB64n    # Job name
#SBATCH --output=runFB64n.out # Stdout (%j expands to jobId)
#SBATCH --error=runFB64n.err # Stderr (%j expands to jobId)
#SBATCH --ntasks=1280     # Number of tasks(processes)
#SBATCH --nodes=64     # Number of nodes requested
#SBATCH --ntasks-per-node=20     # Tasks per node
#SBATCH --cpus-per-task=1     # Threads per task
#SBATCH --time=04:00:00   # walltime
#SBATCH --partition=compute    # Partition
#SBATCH --account=pa220401    # Replace with your system project

cd /users/pa23/goumas/fbran/FB-Thesis/custom-jacobi

## LOAD MODULES ##
module purge # clean up loaded modules

# load necessary modules
module load gnu/8
module load cuda/10.1.168
module load openmpi/4.0.5/gnu

## RUN YOUR PROGRAM ##

problemSizeX=(4096 8192 8192 10240)
problemSizeY=(8192 8192 16384 16384)

Px=(16 16 32 32)
Py=(16 32 32 40)

NumPr=(256 512 1024 1280)

for iVersion in CompBoundJacobi MemBoundJacobi; do
  for idx in "${!problemSizeX[@]}"; do
    for iSize in 128 2048 16384 65536 131072; do
      for iNumMessages in 1 2 4; do
        for iIters in 16; do
          mpirun -np "${NumPr[$idx]}" --map-by socket ./$iVersion \
            "${problemSizeX[$idx]}" "${problemSizeY[$idx]}" \
            "${Px[$idx]}" "${Py[$idx]}" $iSize $iNumMessages $iIters 64
        done
      done
    done
  done
done
