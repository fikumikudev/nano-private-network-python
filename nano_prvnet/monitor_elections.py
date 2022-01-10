import logging
import random
import time
from datetime import datetime

import nano
from rich import box, layout
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from .common import *


def get_active_elections():
    r = rpc.call(action="confirmation_active")
    return r["confirmations"]


def get_active_election_info(root):
    r = rpc.call(action="confirmation_info", params={"json_block": "true", "root": root, "representatives": "true"})
    return r["blocks"]


def generate_data():
    active = get_active_elections()

    info = [get_active_election_info(e) for e in active]

    return Pretty(info)

    pass


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--rpc_host", default="node-main")
    parser.add_argument("--rpc_port", default=17076)

    global args
    args = parser.parse_args()

    global rpc
    rpc = create_rpc_client(args.rpc_host, args.rpc_port)

    global console
    console = Console()

    with Live(console=console, screen=True, auto_refresh=False) as live:
        while True:
            try:
                data = generate_data()

                p = Panel(
                    data, padding=0, title=f"[b]nano private network monitor ('{args.rpc_host}')", subtitle=str(datetime.now().ctime())
                )

                live.update(p, refresh=True)
            except:
                pass

            time.sleep(0.25)
