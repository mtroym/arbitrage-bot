# arbitrage-bot
arbitrage bot built on web3py.

## installation

`$ make install` after this please go arround steps below:

1. prepare an alchemy api key if you want to use alchemy endpoint. 
2. change `.env` file vars to make it works.
3. check configs and add chain config if you want.

## check supported chains

`$ make network`

## run

`$ make run` to run monitor with default `'eth_mainnet'`

or

`$ make run CHAIN_OPTION=<chain_name_from last step>` to query customized network data.

## current features

1. customized providers with alchemy supported.
2. scanning each block
3. scanning block in batch