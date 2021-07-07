from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if rank > 0:
    # Receive data
    data = comm.recv(source=rank-1)
    print(f"Rank {rank} received {data} from rank {rank-1}")

if rank < size - 1:
    comm.send(rank**2, dest=rank+1)