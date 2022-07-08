# Sintra NFT Service

Sintra NFT services respresents module for ingestion, transformation and indexing of blockchain transactions.
Transaction data is acquired through JSON RPC endpoints as hex hash string.

## Getting Started

Prerequisites:

- Python 3.8
- Poetry
- docker-compose

Poetry installation steps are on the following [link](https://python-poetry.org/docs/#installation).

### Installation

After poetry installation, create virtual environment with Python 3.8.
`venv` module, or some of the other virtual environment
packages such as `virtualenv`.

Activate the virtual environment and run

```bash
$ poetry install
```

The existing `poetry.lock` file is used to pin required dependency versions.

### Workers

Worker can be started with

```bash
$ python -m sintra.worker
```

This will start worker configured with [default settings](./sintra/settings.toml).

## Indexers

Indexers and other tools for NFT data ingestion and APIs.

References:

- https://github.com/SecretDuckSociety/TwitterNFTSalesBot
- https://github.com/primenumsdev/solana-nft-tools

Notes:

1. This is the Candy Machine Creation transaction, if we analyze the transaction then we could get the authority (update
   authority) which could be used to identify a collection.

https://solscan.io/tx/5mJkcez9QgCMRVtFH9GqtrogLi3asMBWyQWjPc4uKBfBpeS6b2oJmJuW14L2LXWXdRF6VMHy2HzJyBPTYJddVWTq

## Local Dev Notes (Obsolete, need cleanup)

### Ports

### Command ./main

```
$ ./main web <params>
```

To start local API server

```
$ ./main ws <params>
```

To start local async Websocket listeners. Use there are sub commands to it.

Otherwise, will trigger the click commands in `main.py`.
