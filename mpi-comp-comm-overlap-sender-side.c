#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <time.h>
#include <stdbool.h>

typedef struct input_param {
	int msg_bytes;
	double avg_xfer_usecs;
	double max_xfer_usecs;
} t_input_params;

#define call_mpi( func, ...) { 											\
	int mpi_call_res;													\
	mpi_call_res = func(__VA_ARGS__);									\
	if( mpi_call_res != MPI_SUCCESS ) {									\
		fprintf(stderr, "errot at mpi call on loc=%d\n", __LINE__ );	\
		exit(1); 														\
	}																	\
 }

#define call_clk_gt( func, ...) {										\
 	res = func(__VA_ARGS__);  											\
	if( res != 0 ) { 													\
		fprintf(stderr, "error at clockgettime, loc=%d\n", __LINE__ );	\
		exit(1); 														\
	}																	\
}

#define MAX_MSG_SIZE 4194304 // 4 MB

void cbarrier(int rank) {
	//call_mpi(MPI_Barrier, MPI_COMM_WORLD);

	if( rank == 0 ) {
		call_mpi(MPI_Send, NULL, 0, MPI_INT, 1, 1234, MPI_COMM_WORLD);
		call_mpi(MPI_Recv, NULL, 0, MPI_INT, 1, 1234, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
	} else {
		call_mpi(MPI_Recv, NULL, 0, MPI_INT, 0, 1234, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
		call_mpi(MPI_Send, NULL, 0, MPI_INT, 0, 1234, MPI_COMM_WORLD);
		
	}
	return ;
}

double __attribute__((optimize("O0"))) get_clock_gettime_call_duration(void) {
	struct timespec t_start_total, t_end_total;
	struct timespec timestamp;
	int num_of_iterations, i;
	volatile int res;
	double avg_gtof_call_duration_usecs;

	num_of_iterations = 10000;

	call_clk_gt( clock_gettime, CLOCK_MONOTONIC, &t_start_total );
	for(i=0; i<num_of_iterations; ++i) {

		call_clk_gt(clock_gettime, CLOCK_MONOTONIC, &timestamp );

	}
	call_clk_gt( clock_gettime, CLOCK_MONOTONIC, &t_end_total );

	avg_gtof_call_duration_usecs = (t_end_total.tv_sec - t_start_total.tv_sec)*1000000.0 + (t_end_total.tv_nsec - t_start_total.tv_nsec)/1000.0;
	avg_gtof_call_duration_usecs = avg_gtof_call_duration_usecs/num_of_iterations;

	return avg_gtof_call_duration_usecs;
}

int __attribute__((optimize("O0"))) compute_emulation(double compute_duration_usecs) {

	struct timespec t_start_total, t_end_total;
	volatile double ival_elapsed_usecs = 0.0;
	int res;

	call_clk_gt( clock_gettime, CLOCK_MONOTONIC, &t_start_total );
	while( ival_elapsed_usecs <= compute_duration_usecs) {
		call_clk_gt( clock_gettime, CLOCK_MONOTONIC, &t_end_total );
		ival_elapsed_usecs = (t_end_total.tv_sec - t_start_total.tv_sec)*1000000.0 + (t_end_total.tv_nsec - t_start_total.tv_nsec)/1000.0;
	}
	return 0;
}

void test_compute_emulation(void) {
	struct timespec t_start, t_end;
	int res;

	call_clk_gt( clock_gettime, CLOCK_MONOTONIC, &t_start );	
	compute_emulation(23000);
	call_clk_gt( clock_gettime, CLOCK_MONOTONIC, &t_end );	
	
	printf("Duration elapzed = [%lf] usecs\n",  (t_end.tv_sec - t_start.tv_sec)*1000000.0 + (t_end.tv_nsec - t_start.tv_nsec)/1000.0 );
	return ;
}

int extract_avg_msg_xfer_time(int argc, char** argv, t_input_params* input_params) {
	
	if( argc != 4 ) {
		fprintf(stderr, "error: not enough input arguments, average transfer time or msg size is missingg\n");
		return -1.0;
	}
	input_params->msg_bytes = atoi( argv[1] );
	if( input_params->msg_bytes < 0 ) {
		fprintf(stderr, "error: invalid input msg size = [%s]\n", argv[1] );
		return -1.0;
	}

	input_params->avg_xfer_usecs = strtod(argv[2], NULL);
	if( input_params->avg_xfer_usecs == 0 ) {
		fprintf(stderr, "error: invalid input average transfer time = [%s]\n", argv[2] );
		return -1.0;
	}

	input_params->max_xfer_usecs = strtod(argv[3], NULL);
	if( input_params->max_xfer_usecs == 0 ) {
		fprintf(stderr, "error: invalid input max transfer time = [%s]\n", argv[2] );
		return -1.0;
	}

	
	return 0;
}

/* decide wether inserted computation has interfered with communication time */
bool inserted_computation_affects_comm_time(double avg_comm_time_with_comp, double pure_comm_time, double comp_time_incr_timestep) {
	if( avg_comm_time_with_comp >= (pure_comm_time + comp_time_incr_timestep*pure_comm_time) ) {
		//printf("pure_comm_time=%lf, new time =%lf, true\n", pure_comm_time, avg_comm_time_with_comp );
		return true;
	} else {
		//printf("pure_comm_time=%lf, new time =%lf, false\n", pure_comm_time, avg_comm_time_with_comp );
		return false;
	}
}



/* avg_xfer_time: sender side average transfer time (barrier, gettime, issend, wait, gettime) acquired for each message
 *		as an average of N different mpiruns of a benchmark without any interfering computation
 * max_xfer_time: the average (over all N diffferent runs) sender sinde transfer time. It main use is to identify when
 *		computation interferes with the communication: if increase in communication time is past max_xfer_time the
 *		corresponding iteration is recorded as an affected on
 */
double comp_comm_overlap(int rank, int msg_size, double avg_xfer_time, double max_xfer_time) {

	int res, dest, tag, num_of_iterations, iteration, warmup_iterations, comp_iterations;
	short global_bench_termination, local_bench_termination;
	char* msg_buf;
	MPI_Status recv_status;
	struct timespec t_start, t_end;
	double xfer_time_usecs, compute_time_incr_step, current_compute_time_usecs, clock_gettime_call_dur;
	double last_comp_inserted, cco_ratio, last_xfer_time_before_interference_usecs, additional_compute_time;
	MPI_Request issend_request;

	num_of_iterations = 1000;
	warmup_iterations=100;
	xfer_time_usecs = 0.0;
	cco_ratio = -1.0;
	last_xfer_time_before_interference_usecs = 0.0;
	compute_time_incr_step = 0.05;
	additional_compute_time = compute_time_incr_step*avg_xfer_time;
	global_bench_termination = false;
	clock_gettime_call_dur = get_clock_gettime_call_duration();
	comp_iterations = 1;
	current_compute_time_usecs = 0.0;

	msg_buf = (char*)malloc( sizeof(char)*MAX_MSG_SIZE );
	if( msg_buf == NULL ) {
		fprintf(stderr, "error: failed to malloc at %d\n", __LINE__);
		return 1;
	}

	tag = 71023;
	while(global_bench_termination == false ) {
		if( rank == 0 ) {

			local_bench_termination = false;
			additional_compute_time = comp_iterations*compute_time_incr_step*avg_xfer_time;
			current_compute_time_usecs  = additional_compute_time;
			//printf("warning: iteration [%d] for msg size [%d] comp-time [%lf] pure comm time [%lf]\n", comp_iterations, msg_size, current_compute_time_usecs, avg_xfer_time);
			fflush(stdout);

			if( current_compute_time_usecs <= clock_gettime_call_dur) {
				fprintf(stderr, "warning: error: inserted computation (%lf) finer than timer's accuracy (%lf)\n", current_compute_time_usecs, clock_gettime_call_dur);
			}
			xfer_time_usecs = 0.0;

			for(iteration = 0; iteration < num_of_iterations; ++iteration) {

				cbarrier(rank);
				call_clk_gt( clock_gettime, CLOCK_MONOTONIC, &t_start );
				call_mpi(MPI_Issend, msg_buf, msg_size, MPI_CHAR, 1, tag, MPI_COMM_WORLD, &issend_request);
				compute_emulation(current_compute_time_usecs);
				call_mpi(MPI_Wait, &issend_request, MPI_STATUS_IGNORE);
				call_clk_gt( clock_gettime, CLOCK_MONOTONIC, &t_end );
				xfer_time_usecs = xfer_time_usecs + (t_end.tv_sec - t_start.tv_sec)*1000000.0 + (t_end.tv_nsec - t_start.tv_nsec)/1000.0;
			}
			xfer_time_usecs = xfer_time_usecs / num_of_iterations;
			// for sender side overlap, only the sender can conclude that benchmark shall terminate
			local_bench_termination = inserted_computation_affects_comm_time(xfer_time_usecs, avg_xfer_time, compute_time_incr_step);
			//printf("warning: msg size %d, comp-iteration=%d: comp-comm-time=%lf pure-comm-time=%lf\n", msg_size, comp_iterations, xfer_time_usecs, avg_xfer_time);

			if( local_bench_termination == false ) {
				// inserted computation interfered with communication. Communication time increased more than previous max value
				last_xfer_time_before_interference_usecs = xfer_time_usecs;
				last_comp_inserted = current_compute_time_usecs;
			} else {
				//printf("warning: msg size %d, comp-iteration=%d: insrted computation %lf increases pur comm time from %lf to %lf with max being %lf\n",
				//	msg_size, comp_iterations, current_compute_time_usecs, avg_xfer_time, xfer_time_usecs, max_xfer_time);
			}


		} else { // rank = 1

			local_bench_termination = false;
			for(iteration = 0; iteration < num_of_iterations; ++iteration) {
				cbarrier(rank);
				call_mpi(MPI_Recv, msg_buf, msg_size, MPI_CHAR, 0, tag, MPI_COMM_WORLD, &recv_status);
			}

		}
		call_mpi(MPI_Allreduce, &local_bench_termination, &global_bench_termination, 1, MPI_SHORT, MPI_LOR, MPI_COMM_WORLD);
		comp_iterations++;
	}


	if( rank == 0) {
		// compare the new average transfer time with the initial average transfer time
		if( last_xfer_time_before_interference_usecs == 0.0 ) {
			cco_ratio = 0;
		}
		else if( last_xfer_time_before_interference_usecs < avg_xfer_time ) {
			printf("wanring: communication time with interfering computation for msg size = %d (%lf) lower than pure communication time (%lf]). Inserted computation duration=%lf\n", 
				msg_size, last_xfer_time_before_interference_usecs, avg_xfer_time, last_comp_inserted);
			cco_ratio = (last_comp_inserted - (last_xfer_time_before_interference_usecs-avg_xfer_time) )/avg_xfer_time;
		} else {
			//printf("ratio computed with: %lf last xfer time\n", last_xfer_time_before_interference_usecs);
			cco_ratio = (last_comp_inserted - (last_xfer_time_before_interference_usecs-avg_xfer_time) )/avg_xfer_time;
		}
		if( cco_ratio < 0.0 ) {
			printf("warning: strange ratio case: ratio=%lf. Inserted comp=%lf, comm-with-comp=%lf pure-comm-time=%lf\n",
					cco_ratio, last_comp_inserted, last_xfer_time_before_interference_usecs, avg_xfer_time);
		}
	}


	free( msg_buf );
	return cco_ratio;
}

int main(int argc, char** argv) {

	int res, size, proc_name_len, rank;
	char hostname[MPI_MAX_PROCESSOR_NAME];
	t_input_params input_params;
	double cco_ratio;

	cco_ratio = 0.0;
	res = extract_avg_msg_xfer_time(argc, argv, &input_params);
	if( res < 0 ) {
		return 1;
	}


	res = MPI_Init(&argc, &argv);
	call_mpi(MPI_Comm_size, MPI_COMM_WORLD, &size ) ;
	call_mpi(MPI_Comm_rank, MPI_COMM_WORLD, &rank);
	call_mpi(MPI_Get_processor_name, hostname, &proc_name_len);
	//printf("Rank [%d/%d] runs on [%s]\n", rank, size, hostname);
	//test_compute_emulation();
	cco_ratio = comp_comm_overlap(rank, input_params.msg_bytes, input_params.avg_xfer_usecs, input_params.max_xfer_usecs);
	if( rank == 0 ) {
		printf("size=%d cco_ratio=%lf\n",  input_params.msg_bytes, cco_ratio);
	}
	
	call_mpi( MPI_Finalize );
	return 0;
}	
