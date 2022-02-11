def create_sme_table(client, table_name, lsi_timestamp,
                     lsi_nft_name, lsi_et, lsi_eblt,
                     gsi_sme_id, gsi_nft_name, gsi_collection_name):
    client.create_table(
        TableName=table_name,
        AttributeDefinitions=[
            {
                'AttributeName': 'pk',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'btt',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'et',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'eblt',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'sme_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'nft_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'collection_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'name',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'timestamp',
                'AttributeType': 'N'
            },
        ],
        KeySchema=[
            {
                'AttributeName': 'pk',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'btt',
                'KeyType': 'RANGE'
            },
        ],
        LocalSecondaryIndexes=[
            {
                'IndexName': lsi_timestamp,
                'KeySchema': [
                    {
                        'AttributeName': 'pk',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                }
            },
            {
                'IndexName': lsi_nft_name,
                'KeySchema': [
                    {
                        'AttributeName': 'pk',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'name',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                }
            },
            {
                'IndexName': lsi_et,
                'KeySchema': [
                    {
                        'AttributeName': 'pk',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'et',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                }
            },
            {
                'IndexName': lsi_eblt,
                'KeySchema': [
                    {
                        'AttributeName': 'pk',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'eblt',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                }
            },
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': gsi_sme_id,
                'KeySchema': [
                    {
                        'AttributeName': 'sme_id',
                        'KeyType': 'HASH'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            },
            {
                'IndexName': gsi_nft_name,
                'KeySchema': [
                    {
                        'AttributeName': 'nft_id',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            },
            {
                'IndexName': gsi_collection_name,
                'KeySchema': [
                    {
                        'AttributeName': 'collection_id',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            },
        ],
        BillingMode='PAY_PER_REQUEST',
    )
    waiter = client.get_waiter('table_exists')
    waiter.wait(
        TableName='sme',
        WaiterConfig={
            'Delay': 5,
            'MaxAttempts': 3
        }
    )
