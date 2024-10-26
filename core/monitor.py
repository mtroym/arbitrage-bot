from web3.types import BlockData, TxData, TxReceipt
import asyncio
from resource.providers import Web3RPCProvider
from hexbytes import (
    HexBytes,
)
from json import JSONEncoder
import concurrent.futures
import time
import web3.exceptions as web3_exceptions

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

    def handle_new_block_v2(self, block_identifiers: list[int]):
        # Fetch block details
        start = time.time()
        with self.w3.batch_requests() as batch:
            batch.add_mapping({self.w3.eth.get_block: block_identifiers})
            responses = batch.execute()

        txns: list[HexBytes] = [txn for blk in responses for txn in blk["transactions"]]
        txn_count = len(txns)
        print(f"block data from No.{block_identifiers[0]} ", 
              f"to No.{block_identifiers[-1]} w/ {len(txns)} txns")
        if len(txns) <= 0:
            print("skip with empty txns in these block.")
            return
        
        with self.w3.batch_requests() as batch:
            txn_hashes = [txn.to_0x_hex() for txn in txns]
            batch.add_mapping({
                self.w3.eth.get_transaction_receipt: txn_hashes,
                self.w3.eth.get_transaction: txn_hashes
            })
            responses = batch.execute()
            assert len(responses) == 2 * txn_count
        
        rpc_data_latency = time.time() - start 
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            futures = {executor.submit(self.handle_tx_v2,
                                       responses[tx_idx], responses[txn_count + tx_idx])
                       for tx_idx in range(txn_count)}
            for f in concurrent.futures.as_completed(futures):
                f.result()
        processing_latency = time.time() - start
        print("done, rpc latency: {:.2f}s, latency: {:.2f}s, {:.1f}ms/txn".format(
            rpc_data_latency, processing_latency, processing_latency * 1000 / len(txns)))
    
    def handle_tx_v2(self, txn_data: TxData, txn_receipt: TxReceipt):
        Encoder(indent=2).encode(txn_data)
        Encoder(indent=2).encode(txn_receipt)

    def handle_tx(self, txn_hash: str):
        txn_data: TxData = self.w3.eth.get_transaction(txn_hash)
        txn_receipt: TxReceipt = self.w3.eth.get_transaction_receipt(txn_hash)
        # print("from", tx_data["from"], "to", tx_data["to"])
        Encoder(indent=2).encode(txn_data)
        Encoder(indent=2).encode(txn_receipt)
        # print("done txn", txn_hash)

    async def monitor_blocks(self):
        # Get the latest block number
        latest_block = -1
        while True:
            try:
                # Check for new blocks
                current_block = self.w3.eth.block_number
                if current_block <= latest_block and latest_block != -1:
                    await asyncio.sleep(0.1)  # Polling interval
                    continue
                latest_block = latest_block if latest_block > 0 else current_block - 1
                print("current querying lags: {}".format(current_block - latest_block))
                self.handle_new_block_v2(list(range(latest_block+1, current_block+1)))
                print("batch done")
                latest_block = current_block
            except web3_exceptions.Web3RPCError as rpc_err:
                if rpc_err.rpc_response.get("error", {}).get("code") == 429:
                    continue

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.monitor_blocks())
