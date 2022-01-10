import logging
import random
import time
from collections import deque
from datetime import datetime
from math import *

import nano
from rich import box, layout
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.pretty import Pretty
from rich.progress import track
from rich.table import Table

from ..common import *
from ..consts import GENESIS_PRV_KEY


def get_balance(account):
    balance = rpc.account_balance(account)["balance"]
    return balance


def setup_wallet(private_key):
    wallet = rpc.wallet_create()
    account = rpc.wallet_add(wallet, private_key)
    rpc.wallet_representative_set(wallet=wallet, representative=account)

    console.log(f"[rpc]Account: '{account}' in wallet: '{wallet}'")

    return wallet, account


def create_account():
    account = rpc.account_create(wallet=origin_wallet)
    return account


def send_amount(account_from, account_to, amount):
    # console.log(f"[rpc]Sending from: '{account_from}' to: '{account_to}' amount: {amount}")
    h = rpc.send(wallet=origin_wallet, source=account_from, destination=account_to, amount=amount)
    # console.log(f"  [rpc]Hash: '{h}'")
    return h


def do_spam():
    global origin_wallet
    origin_wallet, origin_account = setup_wallet(args.prv_key)
    console.log(f"[debug]Origin account: '{origin_account}'")
    origin_balance = get_balance(origin_account)
    console.log(f"[debug]Origin balance: {origin_balance}")

    q = deque()
    
    spam_amount = int(origin_balance * 0.01)
    console.log(f"[debug]Spam balance: {spam_amount}")
    q.append((origin_account, spam_amount))

    for n in track(range(args.count), description="Spamming...", console=console):
        account, balance = q.popleft()

        while get_balance(account) == 0:
            time.sleep(0.1)

        a1 = create_account()
        a2 = create_account()

        am = floor(balance / 2)
        send_amount(account_from=account, account_to=a1, amount=am)
        send_amount(account_from=account, account_to=a2, amount=am)

        q.append((a1, am))
        q.append((a2, am))

        # time.sleep(1)

    pass


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("count", type=int)
    parser.add_argument("--rpc_host", default="node-main")
    parser.add_argument("--rpc_port", default=17076)
    parser.add_argument("--prv_key", default=GENESIS_PRV_KEY)

    global args
    args = parser.parse_args()

    global rpc
    rpc = create_rpc_client(args.rpc_host, args.rpc_port)

    global console
    console = Console()

    do_spam()
