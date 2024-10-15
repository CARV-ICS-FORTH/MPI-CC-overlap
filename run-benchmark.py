import subprocess, os, sys, string, math, os.path, statistics
from itertools import repeat

max_msg_size = 4*1024*1024
num_of_distinct_mpiruns = 4
noise_level_threshold = 5 # 5%


def print_bench_banner(output_subbench):
	output_subbench = output_subbench.strip()
	llen = len("MPI-CC-overlap," ) + len(output_subbench) + 2*len("/*** ");
	
	header = "/" + "*"*llen + "/"
	print(header)
	print("/***", "MPI-CC-overlap, ", output_subbench, "***/" )
	print(header)


def assess_noise_ssend_single_run():
	mpirun_fname = "/home/stahanov/bin/openmpi-5.0.5/bin/mpirun"
	binary_fname = "mpi-issend-m-msg-s-barrier-s-timer.out"
	makefile_fname = "/home/stahanov/sources/comp-comm-overlap/MPI-CC-overlap/Makefile"

	cmd = "make all &> /dev/null"
	subprocess.call(['make', 'all'],  stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
	

	if( os.path.exists(mpirun_fname) == False ):
		print("File:",  mpirun_fname, "not found")
		sys.exit(1)
	elif( os.path.exists(binary_fname) == False ):
		print("File:",  binary_fname, "not found")
		sys.exit(1)
	elif( os.path.exists(makefile_fname) == False ):
		print("File:",  makefile_fname, "not found")
		sys.exit(1)
	else:
		pass # no file missing

	cmd = mpirun_fname + " -np 2 " + binary_fname
	try:
		p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	except OSError:
 		print("error: popen: not existing file", cmd)
 		sys.exit(1)
	except ValueError:
		print("error: popen: invalid input arguments", cmd)
		sys.exit(1)
	(p_stdout, p_stderr) = p.communicate()
	p_ret_code = p.returncode
	if p_ret_code == None:
		print("popen: ", cmd, "not terminated yet")
	elif p_ret_code <0:
		print("popen: ", cmd, "terminated with signal ", p_ret_code)
	else:
		pass
		#print(p_stderr)

	p_stdout_entries = p_stdout.splitlines()
	p_stderr_entries = p_stderr.splitlines()
	xfer_times_array = []
	xfer_times_dict = {}
	xfer_times_dict[0] = - 1;
	msg_size = 1
	while( msg_size <= max_msg_size ):
		xfer_times_dict[msg_size] = -1
		msg_size = msg_size*2

	for entry in p_stdout_entries:

		tokens = entry.decode('ascii').split()
		msg_size = -1
		avg_latency = -1.0
		values_found = 0
		
		for token in tokens:

			ret = token.find("size")
			if( ret == 0 ):
				msg_size_tokens = token.split("=")
				msg_size = int(msg_size_tokens[1])
				values_found = values_found + 1

			ret = token.find("avg_latency")
			if( ret == 0 ):
				avg_latency_tokens = token.split("=")
				avg_latency = float(avg_latency_tokens[1])
				values_found = values_found + 1
				

		if values_found == 2:
			xfer_times_dict[msg_size] = avg_latency


	# print(xfer_times_dict)
	return xfer_times_dict

def assess_noise_ssend():

	xfer_times_per_run_dict = {}
	num_of_samples_per_msg_size = {}

	# repeat mpirun num_of_distinct_mpiruns times. Populate a dictionary of lists
	for i in range(0,num_of_distinct_mpiruns):
		xfer_time_per_message = assess_noise_ssend_single_run()
		for key in xfer_time_per_message.keys():
			if( i == 0 ):
				xfer_times_per_run_dict[key] = []				
				num_of_samples_per_msg_size[key] = 1
			else:
				num_of_samples_per_msg_size[key] = num_of_samples_per_msg_size[key] + 1
			xfer_times_per_run_dict[key].append( xfer_time_per_message[key] )
		
	# print("Number of samples per message size = ", num_of_samples_per_msg_size)
	#print("Xfer times per message ", xfer_times_per_run_dict);

	# for each message size, calc difference from minimum to maximum transfer time
	print_bench_banner("assert pt2pt-level noise")
	for key in num_of_samples_per_msg_size.keys():	
		min_xfer_time = min( xfer_times_per_run_dict[key] )
		max_xfer_time = max( xfer_times_per_run_dict[key] )
		diff_perc = 100*(max_xfer_time - min_xfer_time) / max_xfer_time
		if( diff_perc >= noise_level_threshold ):
			print("MPI issend times for ", key, " bytes may differ by up to ", diff_perc, "%")

	print_bench_banner("\nassert mean-median deviation")
	for key in num_of_samples_per_msg_size.keys():	
		mean_xfer_time = statistics.mean( xfer_times_per_run_dict[key] )
		median_xfer_time = statistics.median( xfer_times_per_run_dict[key] )
		diff_perc = 100*(mean_xfer_time - median_xfer_time) / median_xfer_time
		if( diff_perc >= noise_level_threshold ):
			printf("Mean transfer time for message size", key, "differs by ", diff_perc, "% from the median")


# main
assess_noise_ssend()
