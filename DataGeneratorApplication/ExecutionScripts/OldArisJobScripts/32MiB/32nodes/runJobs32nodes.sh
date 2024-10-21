#!/bin/bash -l

#SBATCH --job-name=runFB32n    # Job name
#SBATCH --output=runFB32n.out # Stdout (%j expands to jobId)
#SBATCH --error=runFB32n.err # Stderr (%j expands to jobId)
#SBATCH --ntasks=640     # Number of tasks(processes)
#SBATCH --nodes=32     # Number of nodes requested
#SBATCH --ntasks-per-node=20     # Tasks per node
#SBATCH --cpus-per-task=1     # Threads per task
#SBATCH --time=08:00:00   # walltime
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

problemSizeX=(32768 40960) ##16384 32768 32768 40960
problemSizeY=(65536 65536) ##32768 32768 65536 65536

Px=(16 20)
Py=(32 32)

NumPr=(512 640)

for iVersion in CompBoundJacobi; do
  for idx in "${!problemSizeX[@]}"; do
    for iSize in 128 2048 16384 65536 131072; do
      for iNumMessages in 1 2 4; do
        for iIters in 16; do
          mpirun -np "${NumPr[$idx]}" --map-by node ./$iVersion \
            "${problemSizeX[$idx]}" "${problemSizeY[$idx]}" \
            "${Px[$idx]}" "${Py[$idx]}" $iSize $iNumMessages $iIters 32
        done
      done
    done
  done
done
