#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <sys/time.h>
#include "mpi.h"
#include "utils.h"
#include "StencilBenchmark.h"
#include <unistd.h>
#include <utmpx.h>

int main(int argc, char **argv) {
  int rank, size;
  int global[2], local[2]; //global matrix dimensions and local matrix dimensions (2D-domain, 2D-subdomain)
  int global_padded[2];   //padded global matrix dimensions (if padding is not needed, global_padded=global)
  int grid[2];            //processor grid dimensions
  int i, j, t, k;

  //  int global_converged = 0, converged = 0; //flags for convergence, global and per process

  MPI_Datatype dummy;     //dummy datatype used to align user-defined datatypes in memory

  struct timeval tTotalS, tTotalF, tCompS, tCompF, tCommS, tCommF;//, tDummyCommsS, tDummyCommsF;

  //  , tConvS, tConvF;   //Timers: total-> tts,ttf, computation -> tcs,tcf
  //  double tConv = 0, conv_time,

  double tComm = 0, tTotal = 0, tComp = 0, total_time, comp_time, comms_time;//, dummyComms_time, tDummyComms = 0;

  // Global matrix, local current and previous matrices, pointer to swap between current and previous
  double **U, **u_current, **u_previous, **swap, *uStart;

  MPI_Init(&argc, &argv);
  MPI_Comm_size(MPI_COMM_WORLD, &size);
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);

  //----Read 2D-domain dimensions and process grid dimensions from stdin----//

  int msgSize, numMessages, iterations, numNodes;
  char *workingSetSize;

  if (argc != 9) {
    fprintf(stderr, "Check Input Parameters\n");
    exit(-1);
  } else {
    global[0] = atoi(argv[1]);
    global[1] = atoi(argv[2]);
    grid[0] = atoi(argv[3]);
    grid[1] = atoi(argv[4]);
    msgSize = atoi(argv[5]);
    numMessages = atoi(argv[6]);
    iterations = atoi(argv[7]);
    numNodes = atoi(argv[8]);
  }

  //----Create 2D-cartesian communicator----//
  //----Usage of the cartesian communicator is optional----//

  MPI_Comm CART_COMM;         //CART_COMM: the new 2D-cartesian communicator
  int periods[2] = {0, 0};       //periods={0,0}: the 2D-grid is non-periodic
  int rank_grid[2];           //rank_grid: the position of each process on the new communicator

  MPI_Cart_create(MPI_COMM_WORLD, 2, grid, periods, 0, &CART_COMM);    //communicator creation
  MPI_Cart_coords(CART_COMM, rank, 2, rank_grid);                  //rank mapping on the new communicator

#ifdef SOCKET_BARRIER
  MPI_Comm socketComm;
  MPI_Comm_split_type(CART_COMM, OMPI_COMM_TYPE_SOCKET, rank, MPI_INFO_NULL, &socketComm);

//  int socketCommRank;
//  MPI_Comm_rank(socketComm, &socketCommRank);
//  char hostname[1024];
//  gethostname(hostname, 1024);
//
//  int cpu = sched_getcpu();
//  printf("Hostname: %s. cpu: %d. Global rank: %d. Socket rank: %d\n",hostname, cpu, rank, socketCommRank);
#endif

  //----Compute local 2D-subdomain dimensions----//
  //----Test if the 2D-domain can be equally distributed to all processes----//
  //----If not, pad 2D-domain----//

  for (i = 0; i < 2; i++) {
    if (global[i] % grid[i] == 0) {
      local[i] = global[i] / grid[i];
      global_padded[i] = global[i];
    } else {
      local[i] = (global[i] / grid[i]) + 1;
      global_padded[i] = local[i] * grid[i];
    }
  }

  //----Allocate global 2D-domain and initialize boundary values----//
  //----Rank 0 holds the global 2D-domain----//
  if (rank == 0) {
    U = allocate2d(global_padded[0], global_padded[1]);
    init2d(U, global[0], global[1]);
  }

  //----Allocate local 2D-subdomains u_current, u_previous----//
  //----Add a row/column on each size for ghost cells----//

  u_previous = allocate2d(local[0] + 2, local[1] + 2);
  u_current = allocate2d(local[0] + 2, local[1] + 2);


  //----Distribute global 2D-domain from rank 0 to all processes----//

  //----Appropriate datatypes are defined here----//

  //----Datatype definition for the 2D-subdomain on the global matrix----//

  MPI_Datatype global_block;
  MPI_Type_vector(local[0], local[1], global_padded[1], MPI_DOUBLE, &dummy);
  MPI_Type_create_resized(dummy, 0, sizeof(double), &global_block);
  MPI_Type_commit(&global_block);

  //----Datatype definition for the 2D-subdomain on the local matrix----//

  MPI_Datatype local_block;
  MPI_Type_vector(local[0], local[1], local[1] + 2, MPI_DOUBLE, &dummy);
  MPI_Type_create_resized(dummy, 0, sizeof(double), &local_block);
  MPI_Type_commit(&local_block);

  //----Rank 0 defines positions and counts of local blocks (2D-subdomains) on global matrix----//
  int *scatteroffset, *scattercounts;
  if (rank == 0) {
    scatteroffset = (int *) malloc(size * sizeof(int));
    scattercounts = (int *) malloc(size * sizeof(int));
    for (i = 0; i < grid[0]; i++)
      for (j = 0; j < grid[1]; j++) {
        scattercounts[i * grid[1] + j] = 1;
        scatteroffset[i * grid[1] + j] = (local[0] * local[1] * grid[1] * i + local[1] * j);
      }
    uStart = &U[0][0];
  }


  //----Rank 0 scatters the global matrix----//

  MPI_Scatterv(uStart, scattercounts, scatteroffset, global_block, &u_previous[1][1], 1, local_block, 0,
               MPI_COMM_WORLD);
  MPI_Scatterv(uStart, scattercounts, scatteroffset, global_block, &u_current[1][1], 1, local_block, 0,
               MPI_COMM_WORLD);

  if (rank == 0)
    free2d(U);

  //----Define datatypes or allocate buffers for message passing----//
  MPI_Datatype col;
  MPI_Type_vector(local[0], 1, local[1] + 2, MPI_DOUBLE, &dummy);
  MPI_Type_create_resized(dummy, 0, sizeof(double), &col);
  MPI_Type_commit(&col);


  //----Find the 4 neighbors with which a process exchanges messages----//

  int north, south, east, west;
  MPI_Cart_shift(CART_COMM, 0, 1, &north, &south);
  MPI_Cart_shift(CART_COMM, 1, 1, &west, &east);

  //---Define the iteration ranges per process-----//

  int i_min, i_max, j_min, j_max, numPadding = 0;

  //Default values for internal processes
  i_min = 1;
  j_min = 1;

  // Add 1 for ghost cells
  i_max = local[0] + 1;
  j_max = local[1] + 1;

  // assume the current process has all 4 neighbours
  int numNeighbours = 4;
  // boundary processes with no padding (beginning of 2D grid)
  // add 1 to exclude boundary cells substract 1 from numNeighbours
  if (north == MPI_PROC_NULL) {
    i_min += 1;
    numNeighbours--;
  }
  if (west == MPI_PROC_NULL) {
    j_min += 1;
    numNeighbours--;
  }
  // boundary processes with padding (end of 2D grid)
  // subtract numPadding+1 which is the number of added cells + 1 for the boundary cells
  if (south == MPI_PROC_NULL) {
    numPadding = global_padded[0] - global[0];
    i_max -= numPadding + 1;
    numNeighbours--;
  }
  if (east == MPI_PROC_NULL) {
    numPadding = global_padded[1] - global[1];
    j_max -= numPadding + 1;
    numNeighbours--;
  }

  double *dummyCommBufferSend, **dummyCommBufferRecv;

  dummyCommBufferSend = calloc(msgSize, sizeof(double));

  dummyCommBufferRecv = allocate2d(numMessages * 2, msgSize);

  for (i = 0; i < msgSize; i++) {
    dummyCommBufferSend[i] = 0.0;
  }
  struct communicationalCoreArgs commArgs = {&numMessages, &msgSize, dummyCommBufferSend, dummyCommBufferRecv, north,
                                             south, east, west, &grid[0], &grid[1], rank_grid, &CART_COMM};

  MPI_Request requests[8];
  MPI_Status reqStatus[8];

  struct computationalCoreArgs compArgs;
  compArgs.i = &i;
  compArgs.j = &j;
  compArgs.iterations = &iterations;

  int timeIterations = 128;
  //----Computational core----//
  gettimeofday(&tTotalS, NULL);
  for (t = 0; t < timeIterations; t++) {

    swap = u_previous;
    u_previous = u_current;
    u_current = swap;
    compArgs.u_current = u_current;
    compArgs.u_previous = u_previous;
    /*Compute and Communicate*/

    gettimeofday(&tCommS, NULL);

    if (numNeighbours > 0) {
      GaussSeidelForeCommCore(&commArgs);
    }

#ifdef SOCKET_BARRIER
    MPI_Barrier(socketComm);
#endif

    gettimeofday(&tCommF, NULL);
    tComm += (tCommF.tv_sec - tCommS.tv_sec) + (tCommF.tv_usec - tCommS.tv_usec) * 0.000001;

    gettimeofday(&tCompS, NULL);

    for (i = i_min; i < i_max; i++) {
      for (j = j_min; j < j_max; j++) {
        ComputationalCore(&compArgs);
      }
    }
    gettimeofday(&tCompF, NULL);

    gettimeofday(&tCommS, NULL);

    if (numNeighbours > 0) {
      GaussSeidelAftCommCore(&commArgs);
    }

#ifdef SOCKET_BARRIER
    MPI_Barrier(socketComm);
#endif

    gettimeofday(&tCommF, NULL);
    tComp += (tCompF.tv_sec - tCompS.tv_sec) + (tCompF.tv_usec - tCompS.tv_usec) * 0.000001;
    tComm += (tCommF.tv_sec - tCommS.tv_sec) + (tCommF.tv_usec - tCommS.tv_usec) * 0.000001;

  }
  gettimeofday(&tTotalF, NULL);

  tTotal = (tTotalF.tv_sec - tTotalS.tv_sec) + (tTotalF.tv_usec - tTotalS.tv_usec) * 0.000001;

  MPI_Reduce(&tTotal, &total_time, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
  MPI_Reduce(&tComp, &comp_time, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
  MPI_Reduce(&tComm, &comms_time, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
  total_time /= grid[0] * grid[1];
  comp_time /= grid[0] * grid[1];
  comms_time /= grid[0] * grid[1];


  //----Rank 0 gathers local matrices back to the global matrix----//

  if (rank == 0) {
    U = allocate2d(global_padded[0], global_padded[1]);
    uStart = &U[0][0];
  }

  MPI_Gatherv(&u_current[1][1], 1, local_block, uStart, scattercounts, scatteroffset, global_block, 0,
              MPI_COMM_WORLD);

  if (rank == 0) {

    char *s = malloc(500 * sizeof(char));
    u_int64_t global0 = (u_int64_t) global[0], global1 = (u_int64_t) global[1];
    u_int64_t grid0 = (u_int64_t) grid[0], grid1 = (u_int64_t) grid[1];

    workingSetSize = calculateSize((global0 * global1 * 8) / (grid0 * grid1));

#ifdef COMP_BOUND
    sprintf(s, "results/GaussSeidel/%dnodes/CompBoundResults_%s_%dx%d_%dn.out", numNodes,
            workingSetSize, grid[0], grid[1], numNodes);
#elif MEM_BOUND
    sprintf(s, "results/GaussSeidel/%dnodes/MemBoundResults_%s_%dx%d_%dn.out", numNodes,
            workingSetSize, grid[0], grid[1], numNodes);
#endif

    FILE *f = fopen(s, "a+");

#ifdef SOCKET_BARRIER
    fprintf(f, "GaussSeidel (Socket Barrier) X %d Y %d Px %d Py %d Iter %d\n"
               "Working Set Size %s\n"
               "Extra Iterations %d\n"
               "Num. Dummy MSGs %d\n"
               "MSG Size %d\n"
               "ComputationTime %lf\n"
               "CommsTime %lf\n"
               "TotalTime %lf midpoint %lf\n",
            global[0], global[1], grid[0], grid[1], t,
            workingSetSize, iterations,
            numMessages, 8 * msgSize, comp_time, comms_time, total_time,
            U[global[0] / 2][global[1] / 2]);
#else
    fprintf(f, "GaussSeidel X %d Y %d Px %d Py %d Iter %d\n"
               "Working Set Size %s\n"
               "Extra Iterations %d\n"
               "Num. Dummy MSGs %d\n"
               "MSG Size %d\n"
               "ComputationTime %lf\n"
               "CommsTime %lf\n"
               "TotalTime %lf midpoint %lf\n",
            global[0], global[1], grid[0], grid[1], t,
            workingSetSize, iterations,
            numMessages, 8 * msgSize, comp_time, comms_time, total_time,
            U[global[0] / 2][global[1] / 2]);
#endif

    fprintf(f, "----------------------------------------\n");
    free(s);
    fclose(f);
    free(workingSetSize);

  }
  if (dummyCommBufferSend) {
    free(dummyCommBufferSend);
  }
  free2d(dummyCommBufferRecv);
  MPI_Finalize();
  return 0;
}
