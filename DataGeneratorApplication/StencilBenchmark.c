#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include "utils.h"
#include "mpi.h"
#include "StencilBenchmark.h"
#include <math.h>

void ComputationalCore(computationalCoreArgs *args) {
#ifdef COMP_BOUND

  for (int i = *args->i_min; i < *args->i_max; i++) {
    for (int j = *args->j_min; j < *args->j_max; j++) {
      int k = 0;
      while (k < *args->iterations) {
        args->u_current[i][j] =
          (args->u_previous[i - 1][j] + args->u_previous[i + 1][j] +
          args->u_previous[i][j - 1] + args->u_previous[i][j + 1]) / 4.0;
        k++;
      }
    }
  }

#elif MEM_BOUND

  for (int i = *args->i_min; i < *args->i_max; i++) {
    for (int j = *args->j_min; j < *args->j_max; j++) {
      args->u_current[i][j] =
        (args->u_previous[i - 1][j] + args->u_previous[i + 1][j] +
        args->u_previous[i][j - 1] + args->u_previous[i][j + 1]) / 4.0;
    }
  }

#endif

}

/*
 *  JacobiCommunicationalCore implements a message exchange for a given mpi process in a 2D communicator.
 *  Communication is done in a counter-clockwise manner starting from the northern neighbor.
 *  If a process is missing a neighbor (i.e. is a border process) then it loops to the bordering
 *  process. Arguments are number of messages, message size (number of doubles),
 *  buffers for outgoing and incoming messages (for non-blocking communication), ranks of neighbors,
 *  dimensions of the communicator and coordinates of the mpi process
 */

void CommunicationalCore(communicationalCoreArgs *args) {

  int countSend = 0, countRecv = 0;
  int requestsIdx = 0, neighbourIdx;

  int tempCoords[2];

  if (args->neighbours[0] == MPI_PROC_NULL) {
    tempCoords[0] = *args->Px - 1;
    tempCoords[1] = args->rank_grid[1];
    MPI_Cart_rank(*args->CART_COMM, tempCoords, &args->neighbours[0]);
  }
  if (args->neighbours[1] == MPI_PROC_NULL) {
    tempCoords[1] = 0;
    tempCoords[0] = args->rank_grid[0];
    MPI_Cart_rank(*args->CART_COMM, tempCoords, &args->neighbours[1]);
  }
  if (args->neighbours[2] == MPI_PROC_NULL) {
    tempCoords[0] = 0;
    tempCoords[1] = args->rank_grid[1];
    MPI_Cart_rank(*args->CART_COMM, tempCoords, &args->neighbours[2]);
  }
  if (args->neighbours[3] == MPI_PROC_NULL) {
    tempCoords[1] = *args->Py - 1;
    tempCoords[0] = args->rank_grid[0];
    MPI_Cart_rank(*args->CART_COMM, tempCoords, &args->neighbours[3]);
  }

  MPI_Request requests[2 * *args->numMessages];
  MPI_Status reqStatus[2 * *args->numMessages];

  while (countSend < *args->numMessages) {

    for (neighbourIdx = 2; neighbourIdx < 6; neighbourIdx++) {
      // open recvs for msgs from south, west, north, east ([idx] mod [number of neighbours] )
      if (countRecv < *args->numMessages) {
        MPI_Irecv(args->dummyCommBufferRecv[countRecv], *args->msgSize, MPI_DOUBLE, args->neighbours[neighbourIdx % 4],
                  0,
                  *args->CART_COMM, &requests[requestsIdx]);
        requestsIdx += 1;
        countRecv += 1;
      }
    }

    // send msgs to north, east, south, west
    for (neighbourIdx = 0; neighbourIdx < 4; neighbourIdx++) {
      if (countSend < *args->numMessages) {
        MPI_Isend(args->dummyCommBufferSend[countSend], *args->msgSize, MPI_DOUBLE, args->neighbours[neighbourIdx], 0,
                  *args->CART_COMM, &requests[requestsIdx]);
        requestsIdx += 1;
        countSend += 1;
      }
    }

  }

  MPI_Waitall(requestsIdx, requests, reqStatus);

}
