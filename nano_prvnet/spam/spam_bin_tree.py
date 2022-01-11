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

    origin_balance = wait_for_balance(origin_account)

    logging.debug(f"Origin account: '{origin_account}' with balance: '{origin_balance}'")

    q = deque()

    spam_amount = int(origin_balance * 0.01)
    logging.debug(f"Spam amount: {spam_amount}")

    seed = nanolib.generate_seed()
    first_account = nanolib.generate_account_id(seed, 1)
    logging.debug(f"First account: '{first_account}' for seed: '{seed}'")

    first_hash = send_amount(
        rpc, wallet_from=origin_wallet, account_from=origin_account, account_to=first_account, amount=spam_amount
    )

    q.append((1, first_account, spam_amount, first_hash))

    difficulty = "0000000000000000"

    for n in track(range(args.count), description="Spamming..."):
        idx, account, balance, link = q.popleft()

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

        block_receive.solve_work(difficulty=difficulty)
        block_receive.sign(prv_key)

        hash_receive = rpc.process(block_receive.json())

        idx1 = idx * 2
        idx2 = idx * 2 + 1
        a1 = nanolib.generate_account_id(seed, idx1)
        a2 = nanolib.generate_account_id(seed, idx2)

        am = floor(balance / 2)

        block_1 = nanolib.Block(
            block_type="state",
            account=account,
            representative=account,
            # This is the second block in our account-specific blockchain,
            # so we need to refer to the previous block
            previous=hash_receive,
            # We're sending 500000000000000000000000 raw to our other account,
            # leaving us with 500000000000000000000000 raw in this account
            balance=am,
            # In this case, 'link_as_account' corresponds to the recipient
            link_as_account=a1,
        )

        block_1.solve_work(difficulty=difficulty)
        block_1.sign(prv_key)

        hash_1 = rpc.process(block_1.json())

        block_2 = nanolib.Block(
            block_type="state",
            account=account,
            representative=account,
            # This is the second block in our account-specific blockchain,
            # so we need to refer to the previous block
            previous=hash_1,
            # We're sending 500000000000000000000000 raw to our other account,
            # leaving us with 500000000000000000000000 raw in this account
            balance=0,
            # In this case, 'link_as_account' corresponds to the recipient
            link_as_account=a2,
        )

        block_2.solve_work(difficulty=difficulty)
        block_2.sign(prv_key)

        hash_2 = rpc.process(block_2.json())

        q.append((idx1, a1, am, hash_1))
        q.append((idx2, a2, am, hash_2))

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
