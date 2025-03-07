import os

from app.utils import system

SOLANA_RPC_ENDPOINT = system.get_secure_env('SOLANA_RPC_ENDPOINT')
SOLANA_RPC_WSS_ENDPOINT = system.get_secure_env('SOLANA_RPC_WSS_ENDPOINT')
SOLANA_RPC_CLUSTER_USERNAME = system.get_secure_env('SOLANA_RPC_CLUSTER_USERNAME')
SOLANA_RPC_CLUSTER_PASSWORD = system.get_secure_env('SOLANA_RPC_CLUSTER_PASSWORD')
SOLANA_RPC_CLUSTER_BASIC_AUTH = (SOLANA_RPC_CLUSTER_USERNAME, SOLANA_RPC_CLUSTER_PASSWORD)

# For Secondary Event Streaming
SOLANA_SME_KINESIS_STREAM = os.environ['SOLANA_SME_KINESIS_STREAM']
# 0 for normal kinesis producer, 1 - log only, 2 - local consumer invoking
SOLANA_SME_PRODUCER_MODE = int(os.getenv('SOLANA_SME_PRODUCER_MODE', '0'))
