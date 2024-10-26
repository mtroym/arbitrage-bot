from core.monitor import BlockMonitorDaemon
from core.resource.providers import Web3RPCProvider
import argparse


def single_chain_monitor():
    parser = argparse.ArgumentParser(description="Config monitor")

    parser.add_argument('--chain', type=str,
                        required=False,
                        default="eth_mainnet",
                        help='Choose network by `make network`'
                        )

    args = parser.parse_args()
    provider = Web3RPCProvider(networks=[args.chain])
    monitor = BlockMonitorDaemon(provider=provider, network=args.chain)
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("Monitoring stopped.")


if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv(".env", verbose=True, override=False)
    single_chain_monitor()
