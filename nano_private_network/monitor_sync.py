import logging
import random
import time

from rich import box
from rich.console import Console
from rich.live import Live
from rich.table import Table

from .common import *


def generate_table(rpc_host, rpc_port, peerCache: PeerCache) -> Table:
    table = Table(box=box.SIMPLE)
    table.add_column("IP")
    table.add_column("Count", justify="right", width=12)
    table.add_column("Cemented", justify="right", width=12)
    table.add_column("Unchecked", justify="right", width=12)

    peers = peerCache.updateAndGetPeers()

    for ip, online in peers:
        count, cemented, unchecked = get_block_stats(ip, rpc_port)
        table.add_row(f"{'[red]' if not online else '[green]'}{ip}", f"{count}", f"{cemented}", f"{unchecked}")

    return table


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--rpc_host", default="node-main")
    parser.add_argument("--rpc_port", default=17076)
    args = parser.parse_args()

    console = Console()

    peerCache = PeerCache(args.rpc_host, args.rpc_port)

    with Live(console=console, screen=True, auto_refresh=False) as live:
        while True:
            live.update(generate_table(args.rpc_host, args.rpc_port, peerCache), refresh=True)
            time.sleep(0.25)
