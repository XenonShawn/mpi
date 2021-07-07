import math
from time import time
from argparse import ArgumentParser

from mpi4py import MPI

# Parse argv
parser = ArgumentParser(description="Calculate the number of prime numbers below an integer N.")
parser.add_argument('limit', metavar='N', type=int)
parser.add_argument('-g', '--groups', type=int, default=0)
parser.add_argument('-v', '--verbose', dest='verbose', action='store_const', const=True, default=False)
argv = parser.parse_args()

### Prime Checking Functions ###

def checkPrime(num: int) -> bool:
    """
    First checks if the number is divisible by two, then by every odd number up to the square root of `num`.
    """
    if not num & 1:
        return False 
    for i in range(3, math.isqrt(num) + 1, 2):
        if not num % i:
            return False
    return True

def countPrimes(start: int, stop: int) -> int:
    """
    Returns the number of primes from [start, stop). May by off by one.
    """
    # Primes are -1 or 1 mod 6. Find the first multiple of 6 from `start` onwards.

    mod = start % 6
    if mod or start == 0:
        start += 6 - mod

    numPrimes = 0 if start != 6 else 2
    for n in range(start, stop, 6):
        numPrimes += checkPrime(n-1) + checkPrime(n+1)
    return numPrimes

### Main ###

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nodes = comm.Get_size()

LIMIT = argv.limit
GROUPS = argv.groups or math.ceil(LIMIT / nodes)

if rank == 0:
    # For some reason, all `isend` Request objects have to be stored. Otherwise
    # the garbage collection will affect the buffer sent to the nodes, raising
    # a pickle error.

    # See https://groups.google.com/g/mpi4py/c/ayRwvSslflc

    # If you're just using `send` instead of the asyncrounous `isend`, you don't have
    # any Request objects to store. This will result in a slightly slower execution
    # time of about 10% from my tests, probably from waiting for the nodes to respond.

    send_req = [] # Store `isend` Request objects in a list
    highest = 0
    for i in range(1, nodes):
        req = comm.isend(highest, dest=i)
        send_req.append(req)
        highest = min(GROUPS+highest, LIMIT)
    
    recv_req = [comm.irecv(source=i) for i in range(1, nodes)]
    i = 0
    numPrimes = 0
    while highest < LIMIT:
        # Check if request is done
        done, data = recv_req[i].test()
        if done:
            numPrimes += data['value']

            # Have them do more tasks
            send_req[i] = comm.isend(highest, dest=i+1)
            highest += GROUPS

            # Replace the receive request
            recv_req[i] = comm.irecv(source=i+1)

            if argv.verbose:
                print(f"Rank {i+1} found {data['value']} primes between {data['start']} and {data['stop']} in {data['time']}s")
        i = (i + 1) % len(recv_req)
        
    # Finished, wait for all remaining values to return
    for i in range(len(recv_req)):
        data = recv_req[i].wait()
        numPrimes += data['value']
        send_req[i] = comm.isend(-1, dest=i+1) # Send termination signal
        if argv.verbose:
            print(f"Rank {i+1} found {data['value']} primes between {data['start']} and {data['stop']} in {data['time']}s")

    print(f"Number of primes under {LIMIT}:", numPrimes)
        
else:
    while True:
        start = comm.recv(source=0)
        if start < 0: 
            break # Termination signal
        stop = min(GROUPS+start, LIMIT)
        begin = time()
        value = countPrimes(start, stop)
        comm.send({'value': value, 'time': time()-begin, 'start': start, 'stop': stop}, dest=0)