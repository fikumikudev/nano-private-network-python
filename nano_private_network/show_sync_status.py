import argparse
import logging
from time import sleep
from socket import gethostbyname_ex, inet_aton
import nano

from common import *

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("--rpc_host", default="node")
parser.add_argument("--rpc_port", default=17076)
args = parser.parse_args()


def print_sync_status(rpc_host, rpc_port):
    rpc = create_rpc_client(rpc_host, rpc_port)
    cnt = rpc.block_count()
    logging.info(f"{rpc_host} {cnt['count']}/{cnt['cemented']}")


if __name__ == '__main__':
    ips = get_nodes_on_network(args.rpc_host, args.rpc_port)

    for ip in ips:
        print_sync_status(ip, args.rpc_port)
