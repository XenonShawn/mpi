# My MPI Repository
This repository is meant to include my experiences with mpi4py.

## Installation of MPI4PY
All nodes in the computing cluster have to running the same version of python3, mpi4py, openmpi, etc.

To keep things simple, the following steps were done on Ubuntu 20.04 LTS and its respective Ubuntu Server.
```bash
sudo apt update && sudo apt -y full-upgrade
sudo apt install python3-mpi4py
adduser mpiuser
```

## Usage of MPI4PY
1. The master node has to have a SSH key to all slave nodes. To generate a SSH key,
```bash
ssh-keygen -t rsa

# Repeat the following for every slave node
cat ~/.ssh/id_rsa.pub | ssh mpiuser@IP-ADDRESS "mkdir ~/.ssh; cat >> .ssh/authorized_keys"
```

2. The master node requires a list of all IP addresses of the nodes (including itself).
```bash
nano machines
```

3. A copy of the script to be run must be on each node with the exact same path and name. The `copy` script in this repository is meant to make this process much easier, using the `machines` file made in step 2.

4. To run a script:
```bash
# To run as mpiuser, prefix `sudo -u mpiuser` to the command
mpiexec -hostfile machines --use-hwthread-cpus python3 [absolute path of script]
```