#!/bin/bash -l

#SBATCH --job-name=runExpFB    # Job name
#SBATCH --output=runBySocket80.out # Stdout (%j expands to jobId)
#SBATCH --error=runExpFB.err # Stderr (%j expands to jobId)
#SBATCH --ntasks=40     # Number of tasks(processes)
#SBATCH --nodes=2     # Number of nodes requested
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

problemSizeX=(128)
problemSizeY=(256)

Px=(5)
Py=(8)

NumPr=(40)

for iVersion in CompBoundJacobiSocketBarrier; do
  for idx in "${!problemSizeX[@]}"; do
    for iSize in 128; do
      for iNumMessages in 1; do
        for iIters in 16; do
          mpirun -np "${NumPr[$idx]}" --map-by socket ./$iVersion \
            "${problemSizeX[$idx]}" "${problemSizeY[$idx]}" \
            "${Px[$idx]}" "${Py[$idx]}" $iSize $iNumMessages $iIters 1
        done
      done
    done
  done
done
