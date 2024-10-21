#!/bin/bash -l

#SBATCH --job-name=runFB32n    # Job name
#SBATCH --output=runFB32n.out # Stdout (%j expands to jobId)
#SBATCH --error=runFB32n.err # Stderr (%j expands to jobId)
#SBATCH --ntasks=640    # Number of tasks(processes)
#SBATCH --nodes=32     # Number of nodes requested
#SBATCH --ntasks-per-node=20     # Tasks per node
#SBATCH --cpus-per-task=1     # Threads per task
#SBATCH --time=12:00:00   # walltime
#SBATCH --partition=compute    # Partition
#SBATCH --account=pa220401    # Replace with your system project

cd /users/pa23/goumas/fbran/FB-Thesis/custom-jacobi

## LOAD MODULES ##
module purge # clean up loaded modules

# load necessary modules
module load gnu/8
module load cuda/10.1.168
module load openmpi/4.0.5/gnu

## RUN YOUR PROGRAM 11/11 Done ##

wsSizeMultiplierX=(1 2 4 8 8 16)  ##(16 16 32) ##(1 2 4 8 8 16 16 32)
wsSizeMultiplierY=(1 2 4 8 16 16) ##(16 32 32) ##(1 2 4 8 16 16 32 32)

##problemSizeX=(128 256 256 256)
##problemSizeY=(128 128 256 320)

problemSizeX=(4096 4096 8192 8192 10240)
problemSizeY=(4096 8192 8192 16384 16384)

Px=(8 8 16 16 20)
Py=(8 16 16 32 32)

NumPr=(64 128 256 512 640)

for iVersion in MemBoundJacobi CompBoundJacobi; do ##MemBoundJacobiSocketBarrier ## CompBoundJacobiSocketBarrier
  for mulIdx in "${!wsSizeMultiplierX[@]}"; do
    for idx in "${!problemSizeX[@]}"; do
      for iMsgSizeMul in 5 50; do
        for iNumMessages in 2 4 8; do
          for iIters in 16; do
            declare -i xSize="(${problemSizeX[$idx]} * ${wsSizeMultiplierX[$mulIdx]})"
            declare -i ySize="(${problemSizeY[$idx]} * ${wsSizeMultiplierY[$mulIdx]})"

            mpirun -np "${NumPr[$idx]}" --map-by node ./$iVersion "$xSize" "$ySize" \
              "${Px[$idx]}" "${Py[$idx]}" $iNumMessages $iIters $iMsgSizeMul 32
          done
        done
      done
    done
  done
done
