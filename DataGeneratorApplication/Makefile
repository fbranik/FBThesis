CC=mpicc
CFLAGS=-O3 -lm -Wall
DUMMY_COMM=-DDUMMY_COMM=1
MEM_BOUND=-DMEM_BOUND=1
COMP_BOUND=-DCOMP_BOUND=1
COMP_BOUND_ALT=-DCOMP_BOUND_ALT=1
SOCKET_BARRIER=-DSOCKET_BARRIER=1
GLOBAL_BARRIER=-DGLOBAL_BARRIER=1

#WARMUP=-DWARMUP=1

all: MemBound CompBound

barrier: MemBoundSocketBarrier CompBoundSocketBarrier

standard: CompBoundGlobalBarrier CompBoundSocketBarrier CompBound MemBoundGlobalBarrier MemBoundSocketBarrier MemBound

MemBound: main.c utils.c StencilBenchmark.c
	$(CC) $(CFLAGS) $(DUMMY_COMM) $(MEM_BOUND) main.c utils.c StencilBenchmark.c -o MemBound

CompBound: main.c utils.c StencilBenchmark.c
	$(CC) $(CFLAGS) $(DUMMY_COMM) $(COMP_BOUND) main.c utils.c StencilBenchmark.c -o CompBound

CompBoundAlt: main.c utils.c StencilBenchmark.c
	$(CC) $(CFLAGS) $(DUMMY_COMM) $(COMP_BOUND_ALT) main.c utils.c StencilBenchmark.c -o CompBoundAlt

MemBoundSocketBarrier: main.c utils.c StencilBenchmark.c
	$(CC) $(CFLAGS) $(DUMMY_COMM) $(MEM_BOUND) $(SOCKET_BARRIER) main.c utils.c StencilBenchmark.c -o MemBoundSocketBarrier

CompBoundSocketBarrier: main.c utils.c StencilBenchmark.c
	$(CC) $(CFLAGS) $(DUMMY_COMM) $(COMP_BOUND) $(SOCKET_BARRIER) main.c utils.c StencilBenchmark.c -o CompBoundSocketBarrier

CompBoundGlobalBarrier: main.c utils.c StencilBenchmark.c
	$(CC) $(CFLAGS) $(DUMMY_COMM) $(COMP_BOUND) $(GLOBAL_BARRIER) main.c utils.c StencilBenchmark.c -o CompBoundGlobalBarrier

MemBoundGlobalBarrier: main.c utils.c StencilBenchmark.c
	$(CC) $(CFLAGS) $(DUMMY_COMM) $(MEM_BOUND) $(GLOBAL_BARRIER) main.c utils.c StencilBenchmark.c -o MemBoundGlobalBarrier

MemBoundGaussSeidel: GaussSeidelStencil.c utils.c StencilBenchmark.c
	$(CC) $(CFLAGS) $(DUMMY_COMM) $(MEM_BOUND) GaussSeidelStencil.c utils.c StencilBenchmark.c -o MemBoundGaussSeidel

CompBoundGaussSeidel: GaussSeidelStencil.c utils.c StencilBenchmark.c
	$(CC) $(CFLAGS) $(DUMMY_COMM) $(COMP_BOUND) GaussSeidelStencil.c utils.c StencilBenchmark.c -o CompBoundGaussSeidel

clean:
	rm MemBound CompBound MemBoundSocketBarrier CompBoundSocketBarrier MemBoundGaussSeidel CompBoundGaussSeidel
