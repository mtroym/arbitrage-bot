from web3.types import BlockData, TxData, TxReceipt
import asyncio
from resource.providers import Web3RPCProvider
from hexbytes import (
    HexBytes,
)
from json import JSONEncoder


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

    async def handle_new_block(self, block_identifier):
        # Fetch block details
        block: BlockData = self.w3.eth.get_block(block_identifier)
        txns: list[HexBytes] = block["transactions"]
        print(
            f"New block received: {block['number']} with hash: {block['hash'].hex()}")
        print("txns: {}".format(len(txns)))
        tasks = []
        for txn in txns:
            txn_hash = txn.to_0x_hex()
            task = asyncio.create_task(self.handle_tx(txn_hash))
            tasks.append(task)

        for task in tasks:
            await task

    async def handle_tx(self, txn_hash: str):
        txn_data: TxData = self.w3.eth.get_transaction(
            transaction_hash=txn_hash)
        txn_receicpt: TxReceipt = self.w3.eth.get_transaction_receipt(
            transaction_hash=txn_hash)
        # print("from", tx_data["from"], "to", tx_data["to"])
        print(Encoder(indent=2).encode(txn_data))
        print(Encoder(indent=2).encode(txn_receicpt))

    async def monitor_blocks(self):
        # Get the latest block number
        latest_block = self.w3.eth.block_number
        print(f"Starting monitoring from block: {latest_block}")

        while True:
            # Check for new blocks
            current_block = self.w3.eth.block_number
            print("block lags:", current_block - latest_block)
            if current_block > latest_block:
                for block_query in range(latest_block, current_block):
                    await self.handle_new_block(block_query+1)
                latest_block = current_block

            await asyncio.sleep(0.1)  # Polling interval

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.monitor_blocks())


# Example usage
if __name__ == "__main__":
    provider = Web3RPCProvider(networks=["eth_sepolia"])
    monitor = BlockMonitorDaemon(provider=provider, network="eth_sepolia")
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("Monitoring stopped.")
