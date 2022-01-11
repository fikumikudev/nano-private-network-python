import argparse
import logging
from time import sleep

import nanolib

from .common import *
from .consts import *
from .log_conf import *


def setup_wallet(rpc_host, rpc_port, private_key):
    rpc = create_rpc_client(rpc_host, rpc_port)
    wallet = rpc.wallet_create()
    account = rpc.wallet_add(wallet, private_key)
    rpc.wallet_representative_set(wallet=wallet, representative=account)

    logging.debug(f"Account: '{account}' in wallet: '{wallet}' created on: '{rpc_host}'")

    return wallet, account


def setup_random_wallet(rpc_host, rpc_port):
    rpc = create_rpc_client(rpc_host, rpc_port)
    wallet = rpc.wallet_create()
    account = rpc.account_create(wallet=wallet)
    rpc.wallet_representative_set(wallet=wallet, representative=account)

    logging.debug(f"Account: '{account}' in wallet: '{wallet}' created on: '{rpc_host}'")

    return wallet, account


def get_balance(rpc_host, rpc_port, account):
    rpc = create_rpc_client(rpc_host, rpc_port)
    balance = rpc.account_balance(account)["balance"]
    return balance


def weights_as_percentages(weights):
    s = sum(weights)
    perc = [w / s for w in weights]
    return perc


def wait_all_cemented(rpc):
    while True:
        cnt = rpc.block_count()
        if cnt["count"] == cnt["cemented"] and cnt["unchecked"] == 0:
            break

        sleep(0.1)


def setup_representatives(weights, origin_rpc_host, nodes_rpc_host, rpc_port, genesis_prv_key, reserved_balance):
    logging.info("Setting up representatives...")

    global origin_ip
    origin_ip = resolve_ips(origin_rpc_host)[0]
    logging.debug(f"Origin IP: {origin_ip}")

    node_ips = resolve_ips(nodes_rpc_host)
    logging.debug(f"Node IPs: {node_ips}")

    global origin_wallet, origin_account
    origin_wallet, origin_account = setup_wallet(origin_rpc_host, rpc_port, genesis_prv_key)
    logging.debug(f"Origin account: '{origin_account}'")
    origin_balance = get_balance(origin_rpc_host, rpc_port, origin_account)
    logging.debug(f"Origin balance: {origin_balance}")

    node_wallets = [setup_random_wallet(host, rpc_port) for host in node_ips]
    node_accounts = [account for (wallet, account) in node_wallets]
    logging.debug(f"Created {len(node_wallets)} node wallets")

    net_balance = int(origin_balance * (1 - reserved_balance))
    perc_weights = weights_as_percentages(weights)

    offset = 0

    rpc = create_rpc_client(origin_rpc_host, rpc_port)

    for perc_weight, account in zip(perc_weights, node_accounts):
        amount = int(perc_weight * net_balance) - offset
        offset += 1

        send_amount(rpc, origin_wallet, origin_account, account, amount)

        wait_all_cemented(rpc)

        sleep(5)

    origin_balance = get_balance(origin_rpc_host, rpc_port, origin_account)
    logging.debug(f"Origin balance: {origin_balance}")


def setup_spam_accounts():
    logging.info("Setting up spam accounts...")

    rpc = create_rpc_client(origin_ip, args.rpc_port)

    spam_count = args.spam_count
    logging.debug(f"Spam account count: {spam_count}")

    origin_balance = rpc.account_balance(account=origin_account)["balance"]
    logging.debug(f"Origin balance: {origin_balance}")

    amount = int(origin_balance * args.spam_balance / spam_count)
    logging.debug(f"Spam per account amount: {amount}")

    for i in range(spam_count):
        prv = generate_spam_prv_key(i)
        account = rpc.key_expand(key=prv)["account"]
        logging.debug(f"Spam account: '{account}' from prvkey: '{prv}' for idx: {i}")

        send_amount(rpc, origin_wallet, origin_account, account, amount)

        wait_all_cemented(rpc)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("weights", nargs="+", type=int)
    parser.add_argument("--origin_rpc_host", default="node-main")
    parser.add_argument("--nodes_rpc_host", default="node")
    parser.add_argument("--rpc_port", default=17076)
    parser.add_argument("--genesis_prv_key", default=GENESIS_PRV_KEY)
    parser.add_argument("--reserved_balance", type=float, default=0.1)
    parser.add_argument("--spam_balance", type=float, default=0.1)
    parser.add_argument("--spam_count", type=float, default=32)

    global args
    args = parser.parse_args()

    setup_representatives(
        args.weights,
        args.origin_rpc_host,
        args.nodes_rpc_host,
        args.rpc_port,
        args.genesis_prv_key,
        args.reserved_balance,
    )

    setup_spam_accounts()

    logging.info("Done")
