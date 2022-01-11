python -m nano_prvnet.setup_reps 1 1 1 1 1 1 1 1 1 1

python -m nano_prvnet.spam.spam_bin_tree 100000 --rpc_host=172.18.0.3

python -m nano_prvnet.spam.spam_bin_tree 100000 --rpc_host=172.18.0.


# with docker 

docker build -t nano-prvnet-python .

docker run -it --rm --network="nano-private-network" nano-prvnet-python nano_prvnet.spam.spam_bin_tree 100000 0
