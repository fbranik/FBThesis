#!/bin/bash -l

#SBATCH --job-name=runFB4n    # Job name
#SBATCH --output=runFB4n.out # Stdout (%j expands to jobId)
#SBATCH --error=runFB4n.err # Stderr (%j expands to jobId)
#SBATCH --ntasks=80     # Number of tasks(processes)
#SBATCH --nodes=4     # Number of nodes requested
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

## RUN YOUR PROGRAM##

problemSizeX=(2048 4096 4096 8192)
problemSizeY=(4096 4096 8192 5120)

Px=(4 4 8 8)
Py=(4 8 8 10)

NumPr=(16 32 64 80)

for iVersion in CompBoundJacobi MemBoundJacobi; do
  for idx in "${!problemSizeX[@]}"; do
    for iSize in 128 2048 16384 65536 131072; do
      for iNumMessages in 1 2 4; do
        for iIters in 16; do
          mpirun -np "${NumPr[$idx]}" --map-by socket ./$iVersion \
            "${problemSizeX[$idx]}" "${problemSizeY[$idx]}" \
            "${Px[$idx]}" "${Py[$idx]}" $iSize $iNumMessages $iIters 4
        done
      done
    done
  done
done
