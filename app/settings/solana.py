import os

SOLANA_RPC_ENDPOINT = os.environ['SOLANA_RPC_ENDPOINT']
# SOLANA_RPC_MAINNET_ENDPOINT = os.environ['SOLANA_RPC_MAINNET_ENDPOINT']
# SOLANA_RPC_SERUM_ENDPOINT = os.environ['SOLANA_RPC_SERUM_ENDPOINT']
SOLANA_RPC_WSS_ENDPOINT = os.environ['SOLANA_RPC_WSS_ENDPOINT']

# For Secondary Event Streaming
SOLANA_SME_KINESIS_STREAM = os.environ['SOLANA_SME_KINESIS_STREAM']
# 0 for normal kinesis producer, 1 - log only, 2 - local consumer invoking
SOLANA_SME_PRODUCER_MODE = int(os.getenv('SOLANA_SME_PRODUCER_MODE', '0'))
