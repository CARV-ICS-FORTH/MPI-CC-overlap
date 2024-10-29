all:
	$(mpicc) mpi-send-m-msg-s-barrier-s-timer.c -o mpi-send-m-msg-s-barrier-s-timer.out
	$(mpicc) mpi-ssend-m-msg-s-barrier-s-timer.c -o mpi-ssend-m-msg-s-barrier-s-timer.out
	$(mpicc) mpi-ssend-m-msg-s-barrier-m-timer.c -o mpi-ssend-m-msg-s-barrier-m-timer.out
	$(mpicc) mpi-ssend-m-msg-m-barrier-m-timer.c -o mpi-ssend-m-msg-m-barrier-m-timer.out
	$(mpicc) mpi-issend-m-msg-s-barrier-s-timer.c -o mpi-issend-m-msg-s-barrier-s-timer.out
	$(mpicc) mpi-issend-m-msg-m-barrier-m-timer.c -o mpi-issend-m-msg-m-barrier-m-timer.out
	$(mpicc) mpi-comp-comm-overlap-sender-side.c -o mpi-comp-comm-overlap-sender-side.out
	#/spare/ploumid/apps/ofed-5.8-3.0.7.0/openmpi-4.1.5a1-orig/bin/mpirun --mca pml ucx -x \
	#UCX_NET_DEVICES=mlx5_0:1 --mca btl ^vader,tcp,openib -np 2 --host 192.168.1.130,192.168.1.132 \
	#./mpi-comp-comm-overlap-sender-side.out 16384 7.708605333333333 7.72542	
clean:
	rm *.out
