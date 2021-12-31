import logging
import random
import time
from datetime import datetime

import nano
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from .common import *


def get_reps():
    reps = rpc.representatives()
    reps = {k: v for k, v in sorted(reps.items(), key=lambda item: item[1], reverse=True)}
    return reps


def get_online_reps():
    r = rpc.call(action="representatives_online", params={"weight": "true"})
    reps = r["representatives"] or {}
    reps = {v: int(k["weight"]) for v, k in reps.items()}
    reps = {k: v for k, v in sorted(reps.items(), key=lambda item: item[1], reverse=True)}
    return reps


def generate_data():
    reps = get_reps()
    reps_online = get_online_reps()

    layout = Layout()
    layout.split_column(Panel(Pretty(reps), title="reps"), Panel(Pretty(reps_online), title="online reps"))
    return layout

    # return Pretty(reps)


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
