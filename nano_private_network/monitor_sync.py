import logging
import random
import time
from datetime import datetime

from rich import box, layout
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from .common import *


def generate_table(origin_rpc_host, nodes_rpc_host, rpc_port) -> Table:
    origin_ip = resolve_ips(origin_rpc_host)[0]
    node_ips = resolve_ips(nodes_rpc_host)
    ips = [origin_ip, *node_ips]

    table = Table(box=box.SIMPLE)
    table.add_column("ip")
    table.add_column("count", justify="right")
    table.add_column("cemented", justify="right")
    table.add_column("unchecked", justify="right")
    table.add_column("peers", justify="right")

    origin_peers = get_peers(origin_ip, rpc_port)

    for ip in ips:
        count, cemented, unchecked = get_block_stats(ip, rpc_port)
        online = ip in origin_peers
        peers = get_peers(ip, rpc_port)

        table.add_row(f"{'[red]' if not online else '[green]'}{ip}", f"{count}", f"{cemented}", f"{unchecked}", f"{len(peers)}")

    return table


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--origin_rpc_host", default="node-main")
    parser.add_argument("--nodes_rpc_host", default="node")
    parser.add_argument("--rpc_port", default=17076)
    args = parser.parse_args()

    console = Console()

    with Live(console=console, screen=True, auto_refresh=False) as live:
        while True:
            try:
                table = generate_table(args.origin_rpc_host, args.nodes_rpc_host, args.rpc_port)

                p = Panel(
                    table,
                    padding=0,
                    title="[b]nano private network monitor",
                    subtitle=str(datetime.now().ctime())
                )

                live.update(p, refresh=True)
            except:
                pass

            time.sleep(0.25)
