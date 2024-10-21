#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <sys/time.h>
#include "mpi.h"
#include "utils.h"
#include <utmpx.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include "StencilBenchmark.h"


int main(int argc, char **argv) {
  int rank, size;
  int global[2], local[2]; //global matrix dimensions and local matrix dimensions (2D-domain, 2D-subdomain)
  int global_padded[2];    //padded global matrix dimensions (if padding is not needed, global_padded=global)
  int grid[2];             //processor grid dimensions
  int i, t;

  double tTotal, tComp = 0, tComm = 0;
  struct timeval tTotalS, tTotalF, tCompS, tCompF, tCommS, tCommF;

  double **u_current, **u_previous, **swap;
  MPI_Init(&argc, &argv);
  MPI_Comm_size(MPI_COMM_WORLD, &size);
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);

  int msgSize, numMessages, iterations, numNodes, msgSizeMul;
  char *workingSetSize, *messageSizeString;

  if (argc != 9) {
    fprintf(stderr, "Check Input Parameters\n");
    exit(-1);
  } else {
    global[0] = atoi(argv[1]);
    global[1] = atoi(argv[2]);
    grid[0] = atoi(argv[3]);
    grid[1] = atoi(argv[4]);
    numMessages = atoi(argv[5]);
    iterations = atoi(argv[6]);
    msgSizeMul = atoi(argv[7]);
    numNodes = atoi(argv[8]);
  }

  char *computationTypeAndBarrier = malloc(200 * sizeof(char));

  #ifdef COMP_BOUND
  #ifdef SOCKET_BARRIER
  sprintf(computationTypeAndBarrier, "ComputeBound%dSocketBarrier", iterations);
  #elif GLOBAL_BARRIER
  sprintf(computationTypeAndBarrier, "ComputeBound%dGlobalBarrier", iterations);
  #else
  sprintf(computationTypeAndBarrier, "ComputeBound%dNoBarrier", iterations);
  #endif

  #elif MEM_BOUND
  #ifdef SOCKET_BARRIER
  sprintf(computationTypeAndBarrier, "MemoryBoundSocketBarrier");
  #elif GLOBAL_BARRIER
  sprintf(computationTypeAndBarrier, "MemoryBoundGlobalBarrier");
  #else
  sprintf(computationTypeAndBarrier, "MemoryBoundNoBarrier");
  #endif
  #endif

  //----Create 2D-cartesian communicator----//

  MPI_Comm CART_COMM;
  int periods[2] = {0, 0};
  int rank_grid[2];

  MPI_Cart_create(MPI_COMM_WORLD, 2, grid, periods, 0, &CART_COMM);
  MPI_Cart_coords(CART_COMM, rank, 2, rank_grid);

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

  //----Allocate local 2D-subdomains u_current, u_previous----//
  //----Add a row/column on each size for ghost cells----//

  u_previous = allocate2d(local[0] + 2, local[1] + 2);
  init2d(u_previous, local[0] + 2, local[1] + 2);

  u_current = allocate2d(local[0] + 2, local[1] + 2);
  init2d(u_current, local[0] + 2, local[1] + 2);

  //----Find the 4 neighbors with which a process exchanges messages----//

  int neighbours[4];
  MPI_Cart_shift(CART_COMM, 0, 1, &neighbours[0], &neighbours[2]); // north, south
  MPI_Cart_shift(CART_COMM, 1, 1, &neighbours[3], &neighbours[1]); // east, west

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
  // add 1 to exclude boundary cells subtract 1 from numNeighbours
  if (neighbours[0] == MPI_PROC_NULL) {
    i_min += 1;
    numNeighbours--;
  }
  if (neighbours[3] == MPI_PROC_NULL) {
    j_min += 1;
    numNeighbours--;
  }
  // boundary processes with padding (end of 2D grid)
  // subtract numPadding+1 which is the number of added cells + 1 for the boundary cells
  if (neighbours[2] == MPI_PROC_NULL) {
    numPadding = global_padded[0] - global[0];
    i_max -= numPadding + 1;
    numNeighbours--;
  }
  if (neighbours[1] == MPI_PROC_NULL) {
    numPadding = global_padded[1] - global[1];
    j_max -= numPadding + 1;
    numNeighbours--;
  }

//  double tempSize;
//  tempSize  = (double) local[0] * local[1];
//  msgSize = (int) sqrt(tempSize);

  msgSize = msgSizeMul;

  double **dummyCommBufferSend, **dummyCommBufferRecv;

  dummyCommBufferSend = allocate2d(numMessages, msgSize);

  init2d(dummyCommBufferSend, numMessages, msgSize);

  dummyCommBufferRecv = allocate2d(numMessages, msgSize);

  init2d(dummyCommBufferRecv, numMessages, msgSize);

  struct communicationalCoreArgs commArgs = {&numMessages, &msgSize, dummyCommBufferSend, dummyCommBufferRecv,
                                             neighbours,
                                             &grid[0], &grid[1], rank_grid, &CART_COMM};

  struct computationalCoreArgs compArgs;
  compArgs.i_max = &i_max;
  compArgs.j_max = &j_max;
  compArgs.i_min = &i_min;
  compArgs.j_min = &j_min;
  compArgs.iterations = &iterations;

  u_int64_t global0 = (u_int64_t) global[0], global1 = (u_int64_t) global[1];
  u_int64_t grid0 = (u_int64_t) grid[0], grid1 = (u_int64_t) grid[1];

  workingSetSize = calculateSize((global0 * global1 * 8) / (grid0 * grid1));
  messageSizeString = calculateSize(8 * msgSize);

  char *csvFileName = malloc(500 * sizeof(char));

  time_t filenameTimestamp;
  struct tm *tempTime;
  char *filenameTimestampString = malloc(100 * sizeof(char));

  time(&filenameTimestamp);
  tempTime = localtime(&filenameTimestamp);

  strftime(filenameTimestampString, sizeof(filenameTimestampString), "%Y%m%dT%H%M%S%z", tempTime);

  sprintf(csvFileName, "results/%s_%dn_%d_%s_%d_%s_%s.csv", computationTypeAndBarrier, numNodes,
          grid[0] * grid[1], workingSetSize, numMessages, messageSizeString, filenameTimestampString);

  if (rank == 0) {
    //    Rank 0 writes the header for the outfile
    FILE *f = fopen(csvFileName, "a+");

    fprintf(f,
            "Rank,Total Time,Computation Time,Derived Communication Time,Measured Communication Time,Message Size\n");
    fclose(f);

  }

  int timeIterations = 32;
  //----Computational core----//

  MPI_Barrier(CART_COMM);

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
      CommunicationalCore(&commArgs);
    }

    gettimeofday(&tCommF, NULL);

#ifdef SOCKET_BARRIER
    MPI_Barrier(socketComm);
#endif

#ifdef GLOBAL_BARRIER
    MPI_Barrier(CART_COMM);
#endif

    gettimeofday(&tCompS, NULL);

    ComputationalCore(&compArgs);

    gettimeofday(&tCompF, NULL);

    tComp += (tCompF.tv_sec - tCompS.tv_sec) + (tCompF.tv_usec - tCompS.tv_usec) * 0.000001;

    tComm += (tCommF.tv_sec - tCommS.tv_sec) + (tCommF.tv_usec - tCommS.tv_usec) * 0.000001;
  }

  gettimeofday(&tTotalF, NULL);

  MPI_Barrier(CART_COMM);

  tTotal = (tTotalF.tv_sec - tTotalS.tv_sec) + (tTotalF.tv_usec - tTotalS.tv_usec) * 0.000001;

  MPI_File handle;
  int access_mode = MPI_MODE_WRONLY | MPI_MODE_APPEND;

  if (MPI_File_open(CART_COMM, csvFileName, access_mode, MPI_INFO_NULL, &handle) != MPI_SUCCESS) {
    printf("[MPI process %d] Failure in opening the file.\n", rank);
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }

  char *resultsBuffer = malloc(1000 * sizeof(char));
  MPI_Status status;

  sprintf(resultsBuffer, "%d,%lf,%lf,%lf,%lf,%d\n", rank, tTotal, tComp, tTotal - tComp, tComm, msgSize);
  MPI_File_write_shared(handle, resultsBuffer, strlen(resultsBuffer), MPI_CHAR, &status);

  if (MPI_File_close(&handle) != MPI_SUCCESS) {
    printf("[MPI process %d] Failure in closing the file.\n", rank);
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }

  free(computationTypeAndBarrier);
  free(csvFileName);
  free(filenameTimestampString);
  free(resultsBuffer);
  free(workingSetSize);
  free(messageSizeString);
  free2d(dummyCommBufferRecv);
  free2d(dummyCommBufferSend);
  free2d(u_current);
  free2d(u_previous);

  MPI_Finalize();
  return 0;
}
