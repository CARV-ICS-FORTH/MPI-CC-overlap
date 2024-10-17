all:
	/home/stahanov/bin/openmpi-5.0.5/bin/mpicc mpi-send-m-msg-s-barrier-s-timer.c -o mpi-send-m-msg-s-barrier-s-timer.out
	/home/stahanov/bin/openmpi-5.0.5/bin/mpicc mpi-ssend-m-msg-s-barrier-s-timer.c -o mpi-ssend-m-msg-s-barrier-s-timer.out
	/home/stahanov/bin/openmpi-5.0.5/bin/mpicc mpi-ssend-m-msg-s-barrier-m-timer.c -o mpi-ssend-m-msg-s-barrier-m-timer.out
	/home/stahanov/bin/openmpi-5.0.5/bin/mpicc mpi-ssend-m-msg-m-barrier-m-timer.c -o mpi-ssend-m-msg-m-barrier-m-timer.out
	/home/stahanov/bin/openmpi-5.0.5/bin/mpicc mpi-issend-m-msg-s-barrier-s-timer.c -o mpi-issend-m-msg-s-barrier-s-timer.out
	/home/stahanov/bin/openmpi-5.0.5/bin/mpicc mpi-issend-m-msg-m-barrier-m-timer.c -o mpi-issend-m-msg-m-barrier-m-timer.out
	/home/stahanov/bin/openmpi-5.0.5/bin/mpicc mpi-comp-comm-overlap-sender-side.c -o a.out
	#gcc gettimeofday-dur.c -o gettimeofday-dur.out
	#/home/stahanov/bin/openmpi-5.0.5/bin/mpirun -np 2 mpi-send-m-msg-s-barrier-s-timer.out
	#/home/stahanov/bin/openmpi-5.0.5/bin/mpirun -np 2 mpi-ssend-m-msg-s-barrier-s-timer.out
	#/home/stahanov/bin/openmpi-5.0.5/bin/mpirun -np 2 mpi-ssend-m-msg-s-barrier-m-timer.out
	#/home/stahanov/bin/openmpi-5.0.5/bin/mpirun -np 2 mpi-ssend-m-msg-m-barrier-m-timer.out
	#/home/stahanov/bin/openmpi-5.0.5/bin/mpirun -np 2 mpi-issend-m-msg-s-barrier-s-timer.out
	/home/stahanov/bin/openmpi-5.0.5/bin/mpirun -np 2 a.out 16 0.223 0.900
clean:
	rm *.out
