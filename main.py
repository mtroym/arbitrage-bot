from core.monitor import BlockMonitorDaemon
from core.resource.providers import Web3RPCProvider

def main():
    # Example usage
    provider = Web3RPCProvider(networks=["base_mainnet"])
    monitor = BlockMonitorDaemon(provider=provider, network="base_mainnet")
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("Monitoring stopped.")

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv(".env", verbose=True)
    main()