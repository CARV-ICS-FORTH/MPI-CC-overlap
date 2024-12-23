import subprocess, os, sys, string, math, os.path, statistics, numpy
from itertools import repeat

max_msg_size = 4*1024*1024

def read_and_parse_config():

	input_params = {'mpi_path':None, 'num_of_mpiruns':None, 'num_of_iterations':None, 'max_msg_size':None, 'noise_threshold':None, 'mpirun_args':None}
	# print(input_params)

	input_params_keys = input_params.keys()
	config_fname = os.getcwd() + "/config.in"
	if( os.path.exists(config_fname) == False ):
		print("File:",  config_fname, "not found")
		sys.exit(1)

	config_file = open(config_fname, 'r')
	for line in config_file:
		line = line.rstrip()
		comment_at = line.find('#')
		if( comment_at == 0):
			pass # ignore comments
		else:
			if( comment_at > 0 ):
				param_entry = line[0:comment_at].strip()
			else:
				param_entry = line.strip()
			param_tokens = param_entry.split("=")
			if( len(param_tokens) == 2):
				if( param_tokens[0] in input_params_keys ):
					input_params[ param_tokens[0] ] = param_tokens[1].replace("\"", "")
				else:
					print("warning:", config_fname, ": parameter ", param_tokens[0], "not recognized: ignored")
			else:
				if( param_tokens[0] == "mpirun_args" ):
					mpirun_arg_tokens = param_entry.split("\"")
					input_params[ param_tokens[0] ] = mpirun_arg_tokens[1]
				else:
					print("warning:", config_fname, ": malformed input parameter line ", param_entry, ": ignored")

	none_values = all(input_params.values())

	# check that all required parameters have been specified
	for key in input_params_keys:
		if input_params[key] == None:
			print("error: input configuration parameter ", key, "is missing")
			sys.exit(1)
		if( key == "num_of_mpiruns" or key == "num_of_iterations" or key == "max_msg_size" ):
			if( input_params[key].isnumeric() == False ):
				print("error: input configuration parameter ", key, "requires integer values")
				sys.exit(1)
		elif key == "noise_threshold":
			value = input_params[key].replace(".", "")
			if( value.isnumeric() == False ):

				print("error: input configuration parameter ", key, "requires integer values")
				sys.exit(1)

	#print(input_params)
	# make binaries
	makefile_fname = os.getcwd() + "/Makefile"

	if( os.path.exists(makefile_fname) == False ):
		print("File:",  makefile_fname, "not found")
		sys.exit(1)
	cmd = "make all mpicc=" + input_params["mpi_path"] + "bin/mpicc "
	try:
		p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	except OSError:
		print("error: popen: not existing file", cmd)
		sys.exit(1)
	except ValueError:
		print("error: popen: invalid input arguments", cmd)
		sys.exit(1)

	p.wait()
	p_ret_code = p.returncode
	(p_stdout, p_stderr) = p.communicate()
	p_stderr_entries = p_stderr.splitlines()
	if p_ret_code == None:
		print("popen: ", cmd, "not terminated yet")
	elif p_ret_code <0:
		print("popen: ", cmd, "terminated with signal ", p_ret_code)
	elif p_ret_code >0:
		print("popen: ", cmd, "exits with error code=", p_ret_code)
		for entry in p_stderr_entries:
			print( entry.decode() )
	else:
		pass

	return input_params




def print_bench_banner(output_subbench):
	output_subbench = output_subbench.strip()
	llen = len("MPI-CC-overlap," ) + len(output_subbench) + 2*len("/*** ");
	header = "/" + "*"*llen + "/"
	print(header)
	print("/***", "MPI-CC-overlap, ", output_subbench, "***/" )
	print(header)


def single_benchmark_run(input_params, benchmark_name):
	mpirun_fname = input_params["mpi_path"] + "/bin/mpirun"
	binary_fname = benchmark_name

	if( os.path.exists(mpirun_fname) == False ):
		print("File:",  mpirun_fname, "not found")
		sys.exit(1)
	elif( os.path.exists(binary_fname) == False ):
		print("File:",  binary_fname, "not found")
		sys.exit(1)
	else:
		pass # no file missing

	cmd = mpirun_fname + " " + input_params["mpirun_args"] + " " + binary_fname
	#print(cmd)

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

def mpi_comm_comp_overlap_multiple_mpiruns(input_params, benchmark_name, msg_size, avg_xfer_time, max_xfer_time):
	mpirun_fname = input_params["mpi_path"] + "/bin/mpirun"
	binary_fname = benchmark_name

	if( os.path.exists(mpirun_fname) == False ):
		print("File:",  mpirun_fname, "not found")
		sys.exit(1)
	elif( os.path.exists(binary_fname) == False ):
		print("File:",  binary_fname, "not found")
		sys.exit(1)
	else:
		pass # no file missing

	cmd = mpirun_fname + " " + input_params["mpirun_args"] + " " + binary_fname + " " + str(msg_size) + " " + str(avg_xfer_time) + " " + str(max_xfer_time)
	# cmd = mpirun_fname + " -np 2 " + binary_fname + " " + str(msg_size) + " " + str(avg_xfer_time) + " " + str(max_xfer_time)
	#print(cmd)
	
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
		sys.exit(1)
	elif p_ret_code >0:
		print("popen: ", cmd, "exited with error or warning ", p_ret_code)
		print(p_stderr)
		sys.exit(1)

	p_stdout_entries = p_stdout.splitlines()
	p_stderr_entries = p_stderr.splitlines()
	
	for entry in p_stdout_entries:
		
		if( entry.decode('ascii').find("warning") >= 0):
			print("Mpi bench output: ", entry.decode('ascii') )
		else:
			pass
			#print("Mpi bench output: ", entry.decode('ascii') )
		tokens = entry.decode('ascii').split()
		
		if( len(tokens) != 2):
			continue

		msg_size = -1
		cco_ratio = -1.0
		values_found = 0
		
		for token in tokens:

			ret = token.find("size")
			if( ret == 0 ):
				msg_size_tokens = token.split("=")
				msg_size = int(msg_size_tokens[1])
				values_found = values_found + 1

			ret = token.find("cco_ratio")
			if( ret == 0 ):
				cco_ratio_tokens = token.split("=")
				cco_ratio = float(cco_ratio_tokens[1])
				values_found = values_found + 1
				

		if values_found == 2:
			return cco_ratio

	# print(xfer_times_dict)
	# print("returning -2")
	return -1

def multi_mpiruns(input_params, benchmark_name):
	xfer_times_per_run_dict = {}

	# repeat mpirun num_of_distinct_mpiruns times. Populate a dictionary of lists
	for i in range(0,int(input_params["num_of_mpiruns"]) ):
		xfer_time_per_message = single_benchmark_run(input_params, benchmark_name)
		for key in xfer_time_per_message.keys():
			if( i == 0 ):
				xfer_times_per_run_dict[key] = []				
			else:
				pass
			xfer_times_per_run_dict[key].append( xfer_time_per_message[key] )
		
	return xfer_times_per_run_dict

# a)assess noise for pt2pt message between a pair of processes. Deviation between min and max xfer times larger than
# 	noise_level_threshold are reported
# b)assess presence of outlier values - compare mean and median transfer times over all the num_of_distinct_mpiruns
#	distinct executions of the benchmark
def assess_noise_outliers_ssend(input_params):

	tcomm_pure_dict = multi_mpiruns(input_params, "mpi-isend-m-msg-s-barrier-s-timer.out")

	# for each message size, calc difference from minimum to maximum transfer time
	print_bench_banner("assess pt2pt-level noise")
	for key in tcomm_pure_dict.keys():	
		min_xfer_time = min( tcomm_pure_dict[key] )
		max_xfer_time = max( tcomm_pure_dict[key] )
		diff_perc = 100*(max_xfer_time - min_xfer_time) / max_xfer_time
		if( diff_perc >= float(input_params["noise_threshold"])*100 ):
			print("MPI isend times for ", key, " bytes may differ by up to ", numpy.around(diff_perc,decimals=2), "%", 
				"(min,max) xfer time = (", min_xfer_time, ",", max_xfer_time, ")usecs")


	print_bench_banner("\nassert presence of outlier values")
	for key in tcomm_pure_dict.keys():	
		mean_xfer_time = statistics.mean( tcomm_pure_dict[key] )
		median_xfer_time = statistics.median( tcomm_pure_dict[key] )
		diff_perc = 100*(mean_xfer_time - median_xfer_time) / median_xfer_time
		if( diff_perc >= float(input_params["noise_threshold"])*100 ):
			print("Mean transfer time for message size", key, "differs by ", numpy.around(diff_perc,decimals=2), "% from the median")
	return tcomm_pure_dict

# typical latency or sender-side transfer time benchmark consist of multiple mpi_*send and/or mpi_recv calls
# preceeded by a single barrier call. Time is acquired for the whole block of iterations instead of a per-iteration
# basis. For the comp-comm overlap though, a barrier is needed before each send-recv exchange to ensure ordering of
# processes otherwise idle waiting may be mistaken for computation. On the same direction, timing is performed per
# iteration rather than per-block of sends. This function assess the corresponding intrumentation (barrier + timing)
# overhead by comparing the transfer times for all messages for two different mpi_isend benchmarks
def assess_multi_barrier_timer_effect(input_params, xfer_times_s_timer_s_barrier):
	print_bench_banner("assess instrumentation overhead")
	benchmark_name=os.getcwd() + "/mpi-isend-m-msg-m-barrier-m-timer.out"
	xfer_times_mtimer_mbarrier = multi_mpiruns(input_params, benchmark_name)
	for msg_size in xfer_times_s_timer_s_barrier.keys():

		avg_xfer_time_s_timer_s_barrier = statistics.mean( xfer_times_s_timer_s_barrier[msg_size] )
		avg_xfer_time_m_timer_m_barrier = statistics.mean( xfer_times_mtimer_mbarrier[msg_size] )
		diff = avg_xfer_time_m_timer_m_barrier - avg_xfer_time_s_timer_s_barrier
		abs_diff = abs(diff)/avg_xfer_time_s_timer_s_barrier
		
		if( abs_diff >= float(input_params["noise_threshold"]) ):
			print("MPI_isend communication time for message size", msg_size, "vary by ", numpy.around(100*abs_diff,decimals=2), "% when multipe timers and barriers are used")
			# print("\tSingle-timer-barrier = ", avg_xfer_time_s_timer_s_barrier, "multi-timer-barrier = ", avg_xfer_time_m_timer_m_barrier)

def comp_comm_overlap_ratio_benchmark(input_params, xfer_times_per_run_dict):

	print_bench_banner("\nComp-comm overlap for various message sizes")
	num_of_distinct_mpiruns = int(input_params["num_of_mpiruns"] )
	for msg_size in xfer_times_per_run_dict.keys():
		# print("\tMsg size considered:", msg_size)
		avg_xfer_time = statistics.mean(xfer_times_per_run_dict[msg_size])
		max_xfer_time = max(xfer_times_per_run_dict[msg_size])
		avg_overlap_ratio = 0
		

		#if( msg_size == 16384):
		# 	print(msg_size, avg_xfer_time, max_xfer_time);

		for mpirun_i in range(0, num_of_distinct_mpiruns) :
			benchmark_name = os.getcwd() + "/mpi-comp-comm-overlap-sender-side.out"
			ratio = mpi_comm_comp_overlap_multiple_mpiruns(input_params, benchmark_name, msg_size, avg_xfer_time, max_xfer_time)
			
			avg_overlap_ratio = avg_overlap_ratio + ratio

		avg_overlap_ratio = avg_overlap_ratio/num_of_distinct_mpiruns
		print("Msg size(bytes)=", msg_size, " average comp-comm overlap ratio", numpy.around(avg_overlap_ratio,decimals=2) )
		

# main
input_params=read_and_parse_config()
pur_comm_times_per_run_dict = assess_noise_outliers_ssend(input_params)
assess_multi_barrier_timer_effect(input_params, pur_comm_times_per_run_dict)
comp_comm_overlap_ratio_benchmark(input_params, pur_comm_times_per_run_dict)
