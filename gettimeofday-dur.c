#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(int argc, char** argv) {

	struct timespec t_start_total, t_end_total;
	volatile struct timespec timestamp;
	int num_of_iterations, i, res;
	double avg_gtof_call_duration_usecs;

	num_of_iterations = 10000;

	res = clock_gettime(CLOCK_MONOTONIC, &t_start_total );
	if( res != 0 ) {
		fprintf(stderr, "error: failed at clock_gettime %d\n", __LINE__);
		return 1;
	}
	for(i=0; i<num_of_iterations; ++i) {

		res = clock_gettime(CLOCK_MONOTONIC, &timestamp );
		if( res != 0 ) {
			fprintf(stderr, "error: failed at clock_gettime %d\n", __LINE__);
			return 1;
		}
	}
	res = clock_gettime(CLOCK_MONOTONIC, &t_end_total );
	if( res != 0 ) {
		fprintf(stderr, "error: failed at clock_gettime %d\n", __LINE__);
		return 1;
	}

	avg_gtof_call_duration_usecs = (t_end_total.tv_sec - t_start_total.tv_sec)*1000000.0 + (t_end_total.tv_nsec - t_start_total.tv_nsec)/1000.0;
	avg_gtof_call_duration_usecs = avg_gtof_call_duration_usecs/num_of_iterations;
	printf("average clock_gettime duration=%lf usecs\n", avg_gtof_call_duration_usecs);
}