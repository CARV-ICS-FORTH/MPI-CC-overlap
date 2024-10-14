import subprocess, os, sys, string, math

def assess_noise_ssend():
	cmd = "/home/stahanov/bin/openmpi-5.0.5/bin/mpirun -np 2 mpi-send-m-msg-s-barrier-s-timer.out"
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

	p_stdout_entries = p_stdout.splitlines()
	p_stderr_entries = p_stderr.splitlines()
	xfer_times_array = []
	xfer_times_dict = {}
	xfer_times_dict[0] = - 1;
	msg_size = 1
	while( msg_size <= (4*1024*1024) ):
		print(msg_size)
		msg_size = msg_size*2
		xfer_times_dict[msg_size] = -1

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
				avg_latency = avg_latency_tokens[1]
				values_found = values_found + 1

		if values_found == 2:
			xfer_times_dict[msg_size] = avg_latency


	print(xfer_times_dict)
assess_noise_ssend()