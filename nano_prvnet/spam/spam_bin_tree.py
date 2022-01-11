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
from ..log_conf import *


def get_balance(account):
    balance = rpc.account_balance(account)["balance"]
    return balance


def setup_wallet(private_key):
    wallet = rpc.wallet_create()
    account = rpc.wallet_add(wallet, private_key)
    rpc.wallet_representative_set(wallet=wallet, representative=account)

    logging.debug(f"Account: '{account}' in wallet: '{wallet}'")

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
    spam_idx = args.node_index
    prv_key = generate_spam_prv_key(spam_idx)
    logging.debug(f"Spam private key: '{prv_key}' for idx: {spam_idx}")

    global origin_wallet
    origin_wallet, origin_account = setup_wallet(prv_key)
    logging.debug(f"Origin account: '{origin_account}'")
    origin_balance = get_balance(origin_account)
    logging.debug(f"Origin balance: {origin_balance}")

    q = deque()

    spam_amount = int(origin_balance * 0.01)
    logging.debug(f"Spam balance: {spam_amount}")
    q.append((origin_account, spam_amount))

    for n in track(range(args.count), description="Spamming..."):
        account, balance = q.popleft()

        while get_balance(account) == 0:
            logging.debug(f"Empty account: {account}")
            time.sleep(1)

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

    parser = argparse.ArgumentParser()
    parser.add_argument("count", type=int)
    parser.add_argument("node_index", type=int)
    parser.add_argument("--node", default="node")
    parser.add_argument("--rpc_port", default=17076)

    global args
    args = parser.parse_args()

    ips = resolve_ips(args.node)
    ip = ips[args.node_index]

    logging.info(f"Node ({args.node_index}): {ip}")

    global rpc
    rpc = create_rpc_client(ip, args.rpc_port)

    do_spam()
