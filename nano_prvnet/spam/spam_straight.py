import itertools
import logging
import random
import time
from collections import deque
from datetime import datetime
from math import *

import nano
import nanolib
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
from ..consts import *
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


def wait_for_balance(account):
    bal = 0
    while bal == 0:
        time.sleep(1)
        bal = get_balance(account)
    return bal


def do_spam():
    spam_idx = args.node_index
    spam_prv = generate_spam_prv_key(spam_idx)
    logging.debug(f"Spam prvkey: '{spam_prv}' for idx: {spam_idx}")

    global origin_wallet
    origin_wallet, origin_account = setup_wallet(spam_prv)

    rpc.search_pending_all()

    origin_balance = wait_for_balance(origin_account)

    logging.debug(f"Origin account: '{origin_account}' with balance: '{origin_balance}'")

    spam_amount = int(origin_balance * 0.01 / args.chains)
    logging.debug(f"Spam amount: {spam_amount}")

    chains = []

    for n in range(args.chains):
        seed = nanolib.generate_seed()
        first_account = nanolib.generate_account_id(seed, 0)
        logging.debug(f"First account: '{first_account}' for seed: '{seed}' chain idx: {n}")

        first_hash = send_amount(
            rpc, wallet_from=origin_wallet, account_from=origin_account, account_to=first_account, amount=spam_amount
        )

        chains.append(do_straight_spam(seed, first_hash, spam_amount))

    for n in track(range(args.count), description="Spamming..."):
        for it in chains:
            next(it)


def do_straight_spam(seed, link, balance):
    yield

    for idx in itertools.count():
        account = nanolib.generate_account_id(seed, idx)

        block_receive = nanolib.Block(
            # Use the new universal blocks instead of legacy blocks
            # All universal blocks have the block type 'state' regardless of whether we're
            # sending, receiving or changing the representative
            block_type="state",
            account=account,
            # This can be any valid NANO account, but for simplicity's sake, let's use the
            # same account. Normally, we'll want this representative to be
            # someone trustworthy.
            representative=account,
            # This is the very first block (genesis block) for this account's
            # blockchain, which is why 'previous' is None
            previous=None,
            # The account's initial balance will be 1000000000000000000000000 raw since this
            # is what we received. Your amount may differ; change this field
            # accordingly.
            balance=balance,
            # This is the block in which someone sent us NANO
            link=link,
        )

        prv_key = nanolib.generate_account_private_key(seed, idx)

        block_receive.solve_work(difficulty=DIFFICULTY)
        block_receive.sign(prv_key)

        hash_receive = rpc.process(block_receive.json())

        next_account = nanolib.generate_account_id(seed, idx + 1)

        block_send = nanolib.Block(
            block_type="state",
            account=account,
            representative=account,
            # This is the second block in our account-specific blockchain,
            # so we need to refer to the previous block
            previous=hash_receive,
            # We're sending 500000000000000000000000 raw to our other account,
            # leaving us with 500000000000000000000000 raw in this account
            balance=0,
            # In this case, 'link_as_account' corresponds to the recipient
            link_as_account=next_account,
        )

        block_send.solve_work(difficulty=DIFFICULTY)
        block_send.sign(prv_key)

        link = rpc.process(block_send.json())

        yield


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("count", type=int)
    parser.add_argument("chains", type=int)
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

    global rpc_load_balance
    rpc_load_balance = create_rpc_client(args.node, args.rpc_port)

    do_spam()
