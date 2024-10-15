#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <time.h>

#define call_mpi( func, ...) { 								\
	res = func(__VA_ARGS__);  								\
	if( res != MPI_SUCCESS ) { 								\
		fprintf(stderr, "error on line[%d]\n", __LINE__ );	\
		exit(1); 											\
	}														\
 } 
#define MAX_MSG_SIZE 4194304 // 4 MB

void cbarrier(void) {
	MPI_Barrier(MPI_COMM_WORLD);
}

int main(int argc, char** argv) {

	int res, size, proc_name_len, rank, msg_size, dest, tag, num_of_iterations, iteration;
	char hostname[MPI_MAX_PROCESSOR_NAME];
	char* msg_buf;
	MPI_Status recv_status;
	struct timespec t_start, t_end;
	double xfer_time_usecs;

	num_of_iterations = 10000;
	msg_buf = (char*)malloc( sizeof(char)*MAX_MSG_SIZE );
	if( msg_buf == NULL ) {
		fprintf(stderr, "error: failed to malloc at %d\n", __LINE__);
		return 1;
	}
	res = MPI_Init(&argc, &argv);
	call_mpi(MPI_Comm_size, MPI_COMM_WORLD, &size ) ;
	call_mpi(MPI_Comm_rank, MPI_COMM_WORLD, &rank);
	call_mpi(MPI_Get_processor_name, hostname, &proc_name_len);

	printf("Rank [%d/%d] runs on [%s]\n", rank, size, hostname);

	tag = 81;
	for(msg_size = 0; msg_size <= MAX_MSG_SIZE; msg_size = (msg_size ? msg_size*2 : 1) )  {
		cbarrier();
		if( rank == 0 ) {
			res = clock_gettime(CLOCK_MONOTONIC, &t_start );
			if( res != 0 ) {
				fprintf(stderr, "error: failed to malloc at %d\n", __LINE__);
				return 1;
			}
			for(iteration = 0; iteration < num_of_iterations; ++iteration) {
				call_mpi(MPI_Ssend, msg_buf, msg_size, MPI_CHAR, 1, tag, MPI_COMM_WORLD);
			}
			res = clock_gettime(CLOCK_MONOTONIC, &t_end );
			if( res != 0 ) {
				fprintf(stderr, "error: failed to malloc at %d\n", __LINE__);
				return 1;
			}
		} else { // rank = 1
			for(iteration = 0; iteration < num_of_iterations; ++iteration) {
				call_mpi(MPI_Recv, msg_buf, msg_size, MPI_CHAR, 0, tag, MPI_COMM_WORLD, &recv_status);
			}
		}
		xfer_time_usecs = (t_end.tv_sec - t_start.tv_sec)*1000000.0 + (t_end.tv_nsec - t_start.tv_nsec)/1000.0;
		xfer_time_usecs = xfer_time_usecs/num_of_iterations;
		if( rank == 0) {
			printf("[%s]: avg xfer time: size=%d iters=[%d] avg_latency=%lf usecs\n", argv[0], msg_size, num_of_iterations, xfer_time_usecs);
		}
	}

	free( msg_buf );
	call_mpi( MPI_Finalize );
	return 0;
}	