# MPI-CC-overlap
MPI-CC-overlap is a tool that assess the overlap of computation and communication for the case of MPI non-blocking primitives.
Apart from that:
a)It assess noise in pt2pt message exchanges. It compares min and max average message send times, for all message sizes, across different mpiruns of the benchmark
b)Checks for outlier values in average send times by comparing mean and median average message send times
c)For the case of the computation communication overlap estimation, a single barrier call and two timing calls are used
	per message exchange. For the case of simple send time exploration, barrier and timing are carried only once. The
	third step of the current benchmark suite assess the impact of such a tight timing and barrier-synchronized loop
	of message sends
d)Estimates the computation-communication overlap for various message sizes. For each message size, different mpiruns of
	the benchmark are executed reporting average communication-computation overlap. For the actual benchmark estimation
	the benchmark is mosty based on [1] with some insights from [2].

# Configuring
- For running the benchmark there are two pre-requisits
	- An mpi implementation
	- Specifying parameters in the config.in file
		- mpi_path: the path where mpi is installed. e.g. /usr/bin/openmpi-x/
		- num_of_mpiruns: the number of different mpiruns used to derive average message send and ratio values. More
			distinct mpiruns allow to limite system noise effects
		- num_of_iterations: number of iterations within each different mpi benchmark. Large number of iterations (e.g. 10000)
			are more suitable to avoid any optimized paths for a few message exchanges. Moreover, effect of noise and
			outliers are masked out
		- max_msg_size: the maximum message size tried in posted MPI_Issends. Currently hardcoded to 4MB
		- noise_threshold: controls the results that are output by steps a-c of the benchmark. todo; add more

# Output
- a-c
- ratio
- warnings

# Related studies
1.M. J. Rashti and A. Afsahi, "Assessing the Ability of Computation/Communication Overlap and Communication Progress in Modern Interconnects," 15th Annual IEEE Symposium on High-Performance Interconnects (HOTI 2007), Stanford, CA, USA, 2007, pp. 117-124, doi: 10.1109/HOTI.2007.12
2. A. Denis and F. Trahay, "MPI Overlap: Benchmark and Analysis," 2016 45th International Conference on Parallel Processing (ICPP), Philadelphia, PA, USA, 2016, pp. 258-267, doi: 10.1109/ICPP.2016.37

# Funding Support
We thankfully acknowledge the support of the European Commission and the
Greek General Secretariat for Research and Innovation under the EuroHPC
Programme through the SPACE Centre of Excellence project (Grant Agreement No 101093441).
National contributions from the involved state members (including the Greek
General Secretariat for Research and Innovation) match the EuroHPC
funding.
