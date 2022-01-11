import ipaddress
import logging
import urllib.parse
from socket import gethostbyname_ex, inet_aton

import nano
from nano.rpc import Client

from . import consts


def resolve_ips(host):
    (_, _, ips) = gethostbyname_ex(host)
    s = sorted(ips, key=lambda item: inet_aton(item))
    return s


def create_rpc_client(rpc_host, rpc_port):
    return Client(f"http://{rpc_host}:{rpc_port}")


def parse_hostport(hp):
    # urlparse() and urlsplit() insists on absolute URLs starting with "//"
    result = urllib.parse.urlsplit("//" + hp)
    return result.hostname, result.port


def ipv46_to_ipv4(ip):
    i = ip.replace("::ffff:", "")
    return i


def get_peers(rpc_host, rpc_port):
    rpc = create_rpc_client(rpc_host, rpc_port)
    peers = [ipv46_to_ipv4(parse_hostport(entry)[0]) for entry in rpc.peers().keys()]
    peers = sorted(peers, key=lambda item: inet_aton(item))
    return peers


def get_nodes_on_network(rpc_host, rpc_port):
    peers = get_peers(rpc_host, rpc_port)
    return [rpc_host, *peers]


def get_block_stats(rpc_host, rpc_port):
    rpc = create_rpc_client(rpc_host, rpc_port)
    c = rpc.block_count()
    count = c["count"]
    cemented = c["cemented"]
    unchecked = c["unchecked"]
    return count, cemented, unchecked


def generate_spam_prv_key(index):
    s = f"{index:04d}"
    k = consts.SPAM_PRV_KEY[: -len(s)] + s
    return k


def send_amount(rpc, wallet_from, account_from, account_to, amount):
    # logging.debug(f"Seeding: '{account}' with: {(perc_weight * 100):.1f}% ({amount})")
    logging.debug(f"Seeding: '{account_to}' with: {amount}")
    hash = rpc.send(wallet=wallet_from, source=account_from, destination=account_to, amount=amount)
    logging.debug(f"  Hash: '{hash}'")
    return hash


class PeerCache:
    def __init__(self, rpc_host, rpc_port):
        self.rpc_host = rpc_host
        self.rpc_port = rpc_port
        self._all_peers = set()

    def updateAndGetPeers(self):
        peers = get_peers(self.rpc_host, self.rpc_port)
        self._all_peers.update(set(peers))
        s = sorted(self._all_peers, key=lambda item: inet_aton(item))
        s = [(peer, peer in peers) for peer in s]
        e = [(self.rpc_host, True), *s]
        return e
