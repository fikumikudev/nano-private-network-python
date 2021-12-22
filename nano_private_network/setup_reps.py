import argparse
import logging
from time import sleep

from .common import *
from .console import console
from .consts import *

logging.basicConfig(level=logging.INFO)


def setup_wallet(rpc_host, rpc_port, private_key):
    rpc = create_rpc_client(rpc_host, rpc_port)
    wallet = rpc.wallet_create()
    account = rpc.wallet_add(wallet, private_key)
    return wallet, account


def setup_random_wallet(rpc_host, rpc_port):
    rpc = create_rpc_client(rpc_host, rpc_port)
    wallet = rpc.wallet_create()
    account = rpc.account_create(wallet=wallet)
    return wallet, account


def get_balance(rpc_host, rpc_port, account):
    rpc = create_rpc_client(rpc_host, rpc_port)
    balance = rpc.account_balance(account)["balance"]
    return balance


def send_amount(rpc_host, rpc_port, wallet_from, account_from, account_to, amount):
    rpc = create_rpc_client(rpc_host, rpc_port)
    rpc.send(wallet=wallet_from, source=account_from, destination=account_to, amount=amount)


def weights_as_percentages(weights):
    s = sum(weights)
    perc = [w / s for w in weights]
    return perc


def wait_all_cemented(rpc_host, rpc_port):
    rpc = create_rpc_client(rpc_host, rpc_port)
    while True:
        cnt = rpc.block_count()
        if cnt["count"] == cnt["cemented"] and cnt["unchecked"] == 0:
            break

        sleep(0.1)


def setup_representatives(weights, origin_rpc_host, nodes_rpc_host, rpc_port, genesis_prv_key, reserved_balance):
    origin_ip = resolve_ips(origin_rpc_host)[0]
    console.log(f"[blue]Origin IP: {origin_ip}")

    node_ips = resolve_ips(nodes_rpc_host)
    console.log(f"[blue]Node IPs: {node_ips}")

    origin_wallet, origin_account = setup_wallet(origin_rpc_host, rpc_port, genesis_prv_key)
    console.log(f"[blue]Origin account: {origin_account}")
    origin_balance = get_balance(origin_rpc_host, rpc_port, origin_account)
    console.log(f"[blue]Origin balance: {origin_balance}")

    node_wallets = [setup_random_wallet(host, rpc_port) for host in node_ips]
    node_accounts = [account for (wallet, account) in node_wallets]
    console.log(f"Created {len(node_wallets)} node wallets")

    net_balance = int(origin_balance * (1 - reserved_balance))
    perc_weights = weights_as_percentages(weights)

    for perc_weight, account in zip(perc_weights, node_accounts):
        amount = int(perc_weight * net_balance)

        console.log(f"Sending {(perc_weight * 100):.1f}% ({amount}) to {account}")
        send_amount(origin_rpc_host, rpc_port, origin_wallet, origin_account, account, amount)
        console.log(f"Sent {(perc_weight * 100):.1f}% ({amount}) to {account}")

        wait_all_cemented(origin_rpc_host, rpc_port)

    leftover_origin_balance = get_balance(origin_rpc_host, rpc_port, origin_account)
    console.log(f"Origin leftover balance: {leftover_origin_balance}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("weights", nargs="+", type=int)
    parser.add_argument("--origin_rpc_host", default="node-main")
    parser.add_argument("--nodes_rpc_host", default="node")
    parser.add_argument("--rpc_port", default=17076)
    parser.add_argument("--genesis_prv_key", default=GENESIS_PRV_KEY)
    parser.add_argument("--reserved_balance", type=float, default=0.1)
    args = parser.parse_args()

    with console.status("[bold green]Setting up reps...") as status:
        setup_representatives(
            args.weights,
            args.origin_rpc_host,
            args.nodes_rpc_host,
            args.rpc_port,
            args.genesis_prv_key,
            args.reserved_balance,
        )

        console.log("[bold][red]Done")
