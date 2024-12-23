# MPI-CC-overlap
MPI-CC-overlap is a tool that focuses on assessing the overlap of computation and communication for the case of MPI
non-blocking primitives. Before estimating average computation-communication overlap for each message size it
performs several checks to assess noise and outliers in the actual send message times. Specifically:
## benchmark `mpi-issend-m-msg-s-barrier-s-timer.out`
	- Sender side
	- Extracts pure communication time (issend+wait) for a specific pair of processes and various message sizes
		- Pure communication time = no interfering computation within issend, wait
	- Average extracted over a set of iterations with value fixed in the input configuration
	- Barrier is called once to sync the pair of processes and time is acquired at the sender side twice, before and
		after the batch of iterations
	- Different mpiruns of the same benchmark are carried with actual number fixed through the configuration
	- Compares min and max values over all different mpiruns to assess noise in pt2pt messaging
		- Output dumped for manual inspection
	- Compares mean and median communication times over all different mpiruns as a rough approximation for outliers among
		different mpiruns
		- Output dumped for manual inspection
## benchmark `mpi-issend-m-msg-m-barrier-m-timer.out`
	- Similar to the previous benchmark with the following difference:
	- Instead of a single barrier and timing call for the whole batch of iterations, on each iteration it applies the
		following sequence:
		- barrier, gettime, issend, wait, gettime
	- Compares pure communication time with the previous benchmark to assess extra instrumentation overhead
		- Output dumped for manual inspection
## benchmark `mpi-comp-comm-overlap-sender-side.out`
	- Extracts computation-communication overlap for various message sizes. For each message size, different mpiruns of
		the benchmark are executed reporting average communication-computation overlap. For the actual benchmark estimation
		the benchmark is mosty based on [1] with some insights from [2]

# Output
- Normal ratio values lie in [0,1] where higher is better
- There are a few special cases that may appear and deviate from the normal output produced by the benchmark:
	1. In the computation communication overlap assesmnent benchmark, computation is inserted in between issend and
		the corresponding wait calls. The amount of computation is gradually increased (similar to the approach in [1]).
		The amount of computation inserted is estimated as a fraction of the pure communication time. However, if the
		communication time for a specific pair of messages is finer than the actual time to call `clock_gettime` the
		following wanring will be printed: `error: inserted computation (tc) finer than timer's accuracy (tm)`. The only
		expected scenario for this case is a costly implementation of `clock_gettime`.
	2. Communication ratio = 0: If the first amount of computation inserted already inflates communication time above
		a threshold, the benchmark assumes that it is not possible to overlap computation with communication and returns
		a ratio of 0.
	3. There is an unexpected case where the communication time for a specific message when computation is performed in
		parallel may appear lower than the minimum of pure communication and computation time. This might be due to
		increased noise when acquiring the pure communication or computation time. The output is a ratio value larger than
		one. Such values can be interpreted as perfect overlap

# Configuring & running
- For running the benchmark there are two pre-requisites:
	1. An installation of MPI
	2. Specification of parameters in the **config.in** file:
		- mpi_path: the path where mpi is installed. e.g. /usr/bin/openmpi-x/
		- num_of_mpiruns: the number of different MPI runs used to derive average message send and ratio values. More
			distinct MPI runs allow to limite system noise effects
		- num_of_iterations: number of iterations within each different MPI benchmark. Large number of iterations (e.g. 10000)
			are more suitable to avoid any optimized paths for a few message exchanges. Moreover, effect of noise and
			outliers are masked out
		- max_msg_size: the maximum message size tried in posted MPI_Issend. Currently hardcoded to 4MB
		- noise_threshold: controls the results that are output by steps a-c of the benchmark. 
	3. python3
- For running:
	- ` python3 run-benchmark.py`

# Related studies
1. M. J. Rashti and A. Afsahi, "Assessing the Ability of Computation/Communication Overlap and Communication Progress in Modern Interconnects," 15th Annual IEEE Symposium on High-Performance Interconnects (HOTI 2007), Stanford, CA, USA, 2007, pp. 117-124, doi: 10.1109/HOTI.2007.12
2. A. Denis and F. Trahay, "MPI Overlap: Benchmark and Analysis," 2016 45th International Conference on Parallel Processing (ICPP), Philadelphia, PA, USA, 2016, pp. 258-267, doi: 10.1109/ICPP.2016.37

# Funding Support
We thankfully acknowledge the support of the European Commission and the Greek General Secretariat for Research and Innovation under the EuroHPC Programme through the SPACE Centre of Excellence project (Grant Agreement No 101093441). National contributions from the involved state members (including the Greek General Secretariat for Research and Innovation) match the EuroHPC funding.
