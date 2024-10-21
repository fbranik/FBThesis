#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "utils.h"
#include <inttypes.h>
#include <string.h>

#define DIM(x) (sizeof(x)/sizeof(*(x)))

double max(double a, double b) {
  return a > b ? a : b;
}

int converge(double **u_previous, double **u_current, int i_min, int i_max, int j_min, int j_max) {
  int i, j;
  for (i = i_min; i <= i_max; i++)
    for (j = j_min; j <= j_max; j++)
      if (fabs(u_current[i][j] - u_previous[i][j]) > e) return 0;
  return 1;
}

double **allocate2d(int dimX, int dimY) {
  double **array, *tmp;
  int i;
  u_int64_t dimX0 = (u_int64_t) dimX;
  u_int64_t dimY0 = (u_int64_t) dimY;

  tmp = (double *) calloc(dimX0 * dimY0, sizeof(double));
  array = (double **) calloc(dimX0, sizeof(double *));
  for (i = 0; i < dimX0; i++)
    array[i] = tmp + i * dimY0;
  if (array == NULL || tmp == NULL) {
    fprintf(stderr, "Error in allocation\n");
    exit(-1);
  }
  return array;
}

void free2d(double **array) {
  if (array == NULL) {
    fprintf(stderr, "Error in freeing matrix\n");
    exit(-1);
  }
  if (array[0])
    free(array[0]);
  if (array)
    free(array);
}

void init2d(double **array, int dimX, int dimY) {
  int i, j;
  for (i = 0; i < dimX; i++)
    for (j = 0; j < dimY; j++)
      array[i][j] = ((double) rand() / RAND_MAX) * (100 - 1) + 1;
}

void zero2d(double **array, int dimX, int dimY) {
  int i, j;
  for (i = 0; i < dimX; i++)
    for (j = 0; j < dimY; j++)
      array[i][j] = 0.0;
}

void print2d(double **array, int dimX, int dimY) {
  int i, j;
  for (i = 0; i < dimX; i++) {
    for (j = 0; j < dimY; j++)
      printf("%lf ", array[i][j]);
    printf("\n");
  }
}

void fprint2d(char *s, double **array, int dimX, int dimY) {
  int i, j;
  FILE *f = fopen(s, "w");
  for (i = 0; i < dimX; i++) {
    for (j = 0; j < dimY; j++)
      fprintf(f, "%lf ", array[i][j]);
    fprintf(f, "\n");
  }
  fclose(f);
}

static const char *sizes[] = {"EiB", "PiB", "TiB", "GiB", "MiB", "KiB", "B"};
static const u_int64_t exbibytes = 1024ULL * 1024ULL * 1024ULL *
                                   1024ULL * 1024ULL * 1024ULL;

char *
calculateSize(u_int64_t size) {
  char *result = (char *) malloc(sizeof(char) * 20);
  u_int64_t multiplier = exbibytes;
  int i;

  for (i = 0; i < DIM(sizes); i++, multiplier /= 1024) {
    if (size < multiplier)
      continue;
    if (size % multiplier == 0)
      sprintf(result, "%" PRIu64 "%s", size / multiplier, sizes[i]);
    else
      sprintf(result, "%.1f%s", (float) size / multiplier, sizes[i]);
    return result;
  }
  strcpy(result, "0");
  return result;
}
