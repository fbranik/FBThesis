#include "mpi.h"

struct communicationalCoreArgs {
  int *numMessages;
  int *msgSize;
  double **dummyCommBufferSend;
  double **dummyCommBufferRecv;
  int *neighbours;
  int *Px;
  int *Py;
  int *rank_grid;
  MPI_Comm *CART_COMM;
};
typedef struct communicationalCoreArgs communicationalCoreArgs;


void CommunicationalCore(communicationalCoreArgs *args);

struct computationalCoreArgs {
  int *iterations;
  double **u_current;
  double **u_previous;
  int *i_min, *i_max;
  int *j_min, *j_max;
};
typedef struct computationalCoreArgs computationalCoreArgs;


void ComputationalCore(computationalCoreArgs *args);


void warmupRun(double *commTimeRatio, double **u_current, double **u_previous, double **swap, int *iterations,
               int *i_min, int *j_min, int *i_max, int *j_max, int *local, int *grid,
               MPI_Datatype *col, communicationalCoreArgs *commArgs);