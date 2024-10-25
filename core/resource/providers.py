from typing import Union
from web3 import Web3, HTTPProvider
import json
import os


class ProviderWarpper:
    def __init__(self, conf: dict) -> None:
        self.description = conf.get("description", "-")
        self.endpoint_uri = conf.get("endpoint") \
            .replace("$ALCHEMY_API_KEY", os.getenv("ALCHEMY_API_KEY"))

        self.symbol = conf.get("symbol", "UNK")
        if conf.get("type", "evm") == "evm":
            self.rpc: Web3 = Web3(HTTPProvider(
                endpoint_uri=self.endpoint_uri, request_kwargs={"timeout": 60}))
            self.chain_id = self.rpc.eth.chain_id  # remote chain id
        else:
            raise ValueError(
                "not found provider type: {}".format(conf.get("type")))

        self.name = conf.get("name", conf.get(
            "chain_id", "evm_chain-{}".format(self.chain_id)))

        assert self.chain_id == conf.get("chain_id", self.chain_id), \
            "chain id not match, remote: {}, config: {}".format(
                self.chain_id, conf.get("chain_id"))


class Web3RPCProvider(object):
    def __init__(self, network_conf: dict = None, networks: list = None,
                 default_config_path="configs/networks.json") -> None:
        self.network_conf = network_conf
        if network_conf is None or len(network_conf) == 0:
            f = open(default_config_path, "r")
            self.network_conf = json.load(f)
            f.close()

        self.Rpcs = dict()
        self.network_name_list = networks if networks is not None else []

        for conf in self.network_conf:
            network_name = conf.get("name", None)
            if len(self.network_name_list) != 0 and \
                    (network_name is not None) and (network_name in self.network_name_list):
                p = ProviderWarpper(conf)
                self.Rpcs[p.name] = p

    def get_network_rpc(self, network: str) -> Union[Web3]:
        assert network in self.Rpcs, \
            "missing network {}, you should initialize network first".format(
                network)
        return self.Rpcs[network].rpc

    def get_rpc_list(self) -> list[Web3]:
        return [(n, self.Rpcs[n].rpc) for n in self.Rpcs]


# Example usage
if __name__ == "__main__":
    import json
    import dotenv
    dotenv.load_dotenv(".env", verbose=True)
    rpcs = Web3RPCProvider(
        networks=["eth_sepolia", "opt_sepolia", "base_mainnet"])
    table_member = ["name", "chain_id", "description", "symbol"]
    rows = [
        [rpc.__getattribute__(n) for n in table_member]
        for (_, rpc) in rpcs.Rpcs.items()
    ]
    from tabulate import tabulate
    print(tabulate(rows, headers=table_member))
