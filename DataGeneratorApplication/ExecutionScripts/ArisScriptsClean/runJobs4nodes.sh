#!/bin/bash -l

#SBATCH --job-name=runFB4n    # Job name
#SBATCH --output=runFB4n.out # Stdout (%j expands to jobId)
#SBATCH --error=runFB4n.err # Stderr (%j expands to jobId)
#SBATCH --ntasks=80     # Number of tasks(processes)
#SBATCH --nodes=4     # Number of nodes requested
#SBATCH --ntasks-per-node=20     # Tasks per node
#SBATCH --cpus-per-task=1     # Threads per task
#SBATCH --time=10:00:00   # walltime
#SBATCH --partition=compute    # Partition
#SBATCH --account=pa220401    # Replace with your system project

cd /users/pa23/goumas/fbran/FB-Thesis/custom-jacobi

## LOAD MODULES ##
module purge # clean up loaded modules

# load necessary modules
module load gnu/8
module load cuda/10.1.168
module load openmpi/4.0.5/gnu

wsSizeMultiplierX=(1 2 4 8 8 16)  ##(16 16 32) ##(1 2 4 8 8 16 16 32)
wsSizeMultiplierY=(1 2 4 8 16 16) ##(16 32 32) ##(1 2 4 8 16 16 32 32)

## problemSizeX=(2048 2048 4096 4096 4096)
## problemSizeY=(1024 2048 2048 4096 5120)
##
## Px=(4 4 8 8 8)
## Py=(2 4 4 8 10)
##
## NumPr=(8 16 32 64 80)

problemSizeX=(4096)
problemSizeY=(5120)

Px=(8)
Py=(10)

NumPr=(80)

for iVersion in CompBoundJacobi CompBoundJacobiSocketBarrier CompBoundJacobiGlobalBarrier; do
  for mulIdx in "${!wsSizeMultiplierX[@]}"; do
    for idx in "${!problemSizeX[@]}"; do
      for iMsgSizeMul in 5 50; do
        for iNumMessages in 2 4 8; do
          for iIters in 32; do
            declare -i xSize="(${problemSizeX[$idx]} * ${wsSizeMultiplierX[$mulIdx]})"
            declare -i ySize="(${problemSizeY[$idx]} * ${wsSizeMultiplierY[$mulIdx]})"

            mpirun -np "${NumPr[$idx]}" --map-by node ./$iVersion "$xSize" "$ySize" \
              "${Px[$idx]}" "${Py[$idx]}" $iNumMessages $iIters $iMsgSizeMul 4
          done
        done
      done
    done
  done
done
