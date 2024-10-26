from web3.types import BlockData, TxData, TxReceipt
import asyncio
from resource.providers import Web3RPCProvider
from hexbytes import (
    HexBytes,
)
from json import JSONEncoder
import concurrent.futures
import time


class Encoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, HexBytes):
            return o.to_0x_hex()
        return o.__dict__


class BlockMonitorDaemon:
    def __init__(self, provider: Web3RPCProvider, network):
        self.w3 = provider.get_network_rpc(network=network)
        if not self.w3.is_connected():
            raise Exception("Failed to connect to the Ethereum node.")

    def handle_new_block(self, block_identifier):
        # Fetch block details
        start = time.time()
        block: BlockData = self.w3.eth.get_block(block_identifier)
        txns: list[HexBytes] = block["transactions"]
        print(f"blk No.{block['number']} w/ {len(txns)} txns")
        if len(txns) <= 0:
            print("skip with empty txns in this block.")
            return

        with concurrent.futures.ThreadPoolExecutor(max_workers=24) as executor:
            futures = {executor.submit(self.handle_tx, txn.to_0x_hex())
                       for txn in txns}
            for f in concurrent.futures.as_completed(futures):
                f.result()
        processing_latency = time.time() - start
        print("done, latency: {:.2f}s, {:.1f}ms/txn".format(
            processing_latency, processing_latency * 1000 / len(txns)))

    def handle_tx(self, txn_hash: str):
        txn_data: TxData = self.w3.eth.get_transaction(txn_hash)
        txn_receicpt: TxReceipt = self.w3.eth.get_transaction_receipt(txn_hash)
        # print("from", tx_data["from"], "to", tx_data["to"])
        Encoder(indent=2).encode(txn_data)
        Encoder(indent=2).encode(txn_receicpt)
        # print("done txn", txn_hash)

    async def monitor_blocks(self):
        # Get the latest block number
        latest_block = self.w3.eth.block_number
        print(f"Starting monitoring from block: {latest_block}")

        while True:
            # Check for new blocks
            current_block = self.w3.eth.block_number
            if current_block <= latest_block:
                await asyncio.sleep(0.1)  # Polling interval
                continue

            print("block lags:", current_block - latest_block)
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = {executor.submit(self.handle_new_block, block_query+1)
                           for block_query in range(latest_block, current_block)
                           }
                for f in concurrent.futures.as_completed(futures):
                    f.result()
                print("batch done")
            latest_block = current_block

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.monitor_blocks())


# Example usage
if __name__ == "__main__":
    provider = Web3RPCProvider(networks=["eth_mainnet"])
    monitor = BlockMonitorDaemon(provider=provider, network="eth_mainnet")
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("Monitoring stopped.")
