# sintra-data-service

Indexers and other tools for data ingestion and transformations.

References:

* https://github.com/SecretDuckSociety/TwitterNFTSalesBot
* https://github.com/primenumsdev/solana-nft-tools

Notes:

1. This is the Candy Machine Creation transaction, if we analyze the transaction then we could get the authority (update
   authority) which could be used to identify a collection.

https://solscan.io/tx/5mJkcez9QgCMRVtFH9GqtrogLi3asMBWyQWjPc4uKBfBpeS6b2oJmJuW14L2LXWXdRF6VMHy2HzJyBPTYJddVWTq

## Local Dev Notes:

Admin Ports - Postgres: 8080 - DynamoDB: 8001 - SQS: 9325

## Postgres Migration Commands

```shell
$ ./migration revision --autogenerate -m "<comment>"
...
$ ./migration upgrade <hash> | HEAD
```

To downgrade,

```shell
$ ./migration downgrade -1
```