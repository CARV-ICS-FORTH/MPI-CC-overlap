#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <time.h>

#define call_mpi( func, ...) { 								\
	int mpi_call_res;										\
	mpi_call_res = func(__VA_ARGS__);						\
	if( mpi_call_res != MPI_SUCCESS ) {						\
		fprintf(stderr, "error on line[%d]\n", __LINE__ );	\
		exit(1); 											\
	}														\
 } 
#define MAX_MSG_SIZE 4194304 // 4 MB

void cbarrier(int rank) {
	// MPI_Barrier(MPI_COMM_WORLD);

	if( rank == 0 ) {
		call_mpi(MPI_Send, NULL, 0, MPI_INT, 1, 1234, MPI_COMM_WORLD);
		call_mpi(MPI_Recv, NULL, 0, MPI_INT, 1, 1234, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
	} else {
		call_mpi(MPI_Recv, NULL, 0, MPI_INT, 0, 1234, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
		call_mpi(MPI_Send, NULL, 0, MPI_INT, 0, 1234, MPI_COMM_WORLD);
		
	}
	return ;
}

int main(int argc, char** argv) {

	int res, size, proc_name_len, rank, msg_size, dest, tag, num_of_iterations, iteration, warmup_iterations;
	char hostname[MPI_MAX_PROCESSOR_NAME];
	char* msg_buf;
	MPI_Status recv_status;
	struct timespec t_start, t_end;
	double xfer_time_usecs;
	MPI_Request issend_request;

	num_of_iterations = 10000;
	warmup_iterations = 100;
	xfer_time_usecs = 0.0;
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

	tag = 71023;
	for(msg_size = 0; msg_size <= MAX_MSG_SIZE; msg_size = (msg_size ? msg_size*2 : 1) )  {
		
		if( rank == 0 ) {
			
			for(iteration = 0; iteration < num_of_iterations; ++iteration) {

				cbarrier(rank);
				res = clock_gettime(CLOCK_MONOTONIC, &t_start );
				call_mpi(MPI_Issend, msg_buf, msg_size, MPI_CHAR, 1, tag, MPI_COMM_WORLD, &issend_request);
				call_mpi(MPI_Wait, &issend_request, MPI_STATUS_IGNORE);
				res = clock_gettime(CLOCK_MONOTONIC, &t_end );
				xfer_time_usecs = xfer_time_usecs + (t_end.tv_sec - t_start.tv_sec)*1000000.0 + (t_end.tv_nsec - t_start.tv_nsec)/1000.0;

			}
			
			
		} else { // rank = 1

			for(iteration = 0; iteration < num_of_iterations; ++iteration) {
				cbarrier(rank);
				call_mpi(MPI_Recv, msg_buf, msg_size, MPI_CHAR, 0, tag, MPI_COMM_WORLD, &recv_status);
			}

		}
		
		xfer_time_usecs = xfer_time_usecs/num_of_iterations;
		if( rank == 0) {
			printf("[%s]: avg xfer time: size=%d iters=[%d] avg_latency=%lf usecs\n", argv[0], msg_size, num_of_iterations, xfer_time_usecs);
		}
	}

	free( msg_buf );
	call_mpi( MPI_Finalize );
	return 0;
}	