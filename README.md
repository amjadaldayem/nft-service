# sintra-nft-service

Indexers and other tools for NFT data ingestion and APIs.

References:

* https://github.com/SecretDuckSociety/TwitterNFTSalesBot
* https://github.com/primenumsdev/solana-nft-tools

Notes:

1. This is the Candy Machine Creation transaction, if we analyze the transaction then we could get the authority (update
   authority) which could be used to identify a collection.

https://solscan.io/tx/5mJkcez9QgCMRVtFH9GqtrogLi3asMBWyQWjPc4uKBfBpeS6b2oJmJuW14L2LXWXdRF6VMHy2HzJyBPTYJddVWTq

## Local Dev Notes

### Ports

Postgres: 5432
Postgres Dashboard: 8080
DynamoDB: 8000
DynamoDB Dashboard: 8001
SQS: 9324
SQS Dashboard: 9325
OpenSearch: 9200 (HTTPS!)
OpenSearch Dashboard: 9600

All other AWS Services: 5050

## Postgres Migration Commands

```shell
$ ./migration <db_alias> revision --autogenerate -m "<comment>"
...
$ ./migration <db_alias> upgrade <hash> | HEAD
```


To downgrade,

```shell
$ ./migration <db_alias> downgrade -1
```

Where the `db_alias` is the db alias as defined as the keys in the 
`settings.DATABASES`.