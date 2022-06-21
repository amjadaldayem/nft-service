from typing import Any, Dict, Generator
from unittest.mock import patch

import boto3
import pytest
from src.app import lambda_handler
from src.exception import DecodingException


def transaction_example() -> Dict[str, Any]:
    return {
        "blockTime": 1645939150,
        "meta": {
            "err": None,
            "fee": 5000,
            "innerInstructions": [
                {
                    "index": 0,
                    "instructions": [
                        {
                            "accounts": [1, 3],
                            "data": "bmbDoA7SAcDViY5Sb4cAMcF1SLaKNyaKfxGcH87VnVSt9Xr",
                            "programIdIndex": 4,
                        }
                    ],
                }
            ],
            "logMessages": [
                "Program MEisE1HzehtrDpAAT8PnLHjpSSkRYakotTuJRPjTpo8 invoke [1]",
                "Program TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA invoke [2]",
                "Program log: Instruction: SetAuthority",
                "Program TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA consumed 1770 of 191192 compute units",
                "Program TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA success",
                "Program MEisE1HzehtrDpAAT8PnLHjpSSkRYakotTuJRPjTpo8 consumed 11889 of 200000 compute units",
                "Program MEisE1HzehtrDpAAT8PnLHjpSSkRYakotTuJRPjTpo8 success",
            ],
            "postBalances": [
                7613829240,
                2039280,
                0,
                271587843661,
                953185920,
                1141440,
            ],
            "postTokenBalances": [
                {
                    "accountIndex": 1,
                    "mint": "7VUkpwzNn8s3VTgPAFESmh42aEpk5JqgUVUinSk7Tg3k",
                    "owner": "H4RZVkj7H9q5Q65BMvwctJ1Fnw5f2GQyp3vVB6rnGZpx",
                    "uiTokenAmount": {
                        "amount": "1",
                        "decimals": 0,
                        "uiAmount": 1.0,
                        "uiAmountString": "1",
                    },
                }
            ],
            "preBalances": [
                7612386560,
                2039280,
                1447680,
                271587843661,
                953185920,
                1141440,
            ],
            "preTokenBalances": [
                {
                    "accountIndex": 1,
                    "mint": "7VUkpwzNn8s3VTgPAFESmh42aEpk5JqgUVUinSk7Tg3k",
                    "owner": "GUfCR9mK6azb9vcpsxgXyj7XRPAKJd4KMHTTVvtncGgp",
                    "uiTokenAmount": {
                        "amount": "1",
                        "decimals": 0,
                        "uiAmount": 1.0,
                        "uiAmountString": "1",
                    },
                }
            ],
            "rewards": [],
            "status": {"Ok": None},
        },
        "slot": 122667014,
        "transaction": {
            "message": {
                "accountKeys": [
                    "H4RZVkj7H9q5Q65BMvwctJ1Fnw5f2GQyp3vVB6rnGZpx",
                    "AazL86Qi3dLpkvhTkWMW6cZCZGKz6UN1Go7RaZjdSDid",
                    "6HHrHnDEWuqDM9cgWgtdqkbwSg2Qtff4dK4At7z9qjQX",
                    "GUfCR9mK6azb9vcpsxgXyj7XRPAKJd4KMHTTVvtncGgp",
                    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                    "MEisE1HzehtrDpAAT8PnLHjpSSkRYakotTuJRPjTpo8",
                ],
                "header": {
                    "numReadonlySignedAccounts": 0,
                    "numReadonlyUnsignedAccounts": 3,
                    "numRequiredSignatures": 1,
                },
                "instructions": [
                    {
                        "accounts": [0, 1, 3, 2, 4],
                        "data": "TE6axTojnpk",
                        "programIdIndex": 5,
                    }
                ],
                "recentBlockhash": "5U5q2k1pDgeiqboFHR1UNpNEg9qzC41Pw7AJMnpHCvsT",
            },
            "signatures": [
                "2ofP3EPaGxCuizB4yFfssHHFjnFCoGzQoF3sKQotWVnsZZi24dpbDE8AVuAhjux2cYYKGBrEfnMStYqGNpTtffET"
            ],
        },
    }


def invalid_transaction_example() -> Dict[str, Any]:
    return {
        "blockTime": 1645939150,
        "meta": {
            "err": None,
            "fee": 5000,
            "innerInstructions": [
                {
                    "index": 0,
                    "instructions": [
                        {
                            "accounts": [1, 3],
                            "data": "bmbDoA7SAcDViY5Sb4cAMcF1SLaKNyaKfxGcH87VnVSt9Xr",
                            "programIdIndex": 4,
                        }
                    ],
                }
            ],
            "postBalances": [
                7613829240,
                2039280,
                0,
                271587843661,
                953185920,
                1141440,
            ],
            "postTokenBalances": [
                {
                    "accountIndex": 1,
                    "mint": "7VUkpwzNn8s3VTgPAFESmh42aEpk5JqgUVUinSk7Tg3k",
                    "owner": "H4RZVkj7H9q5Q65BMvwctJ1Fnw5f2GQyp3vVB6rnGZpx",
                    "uiTokenAmount": {
                        "amount": "1",
                        "decimals": 0,
                        "uiAmount": 1.0,
                        "uiAmountString": "1",
                    },
                }
            ],
            "preBalances": [
                7612386560,
                2039280,
                1447680,
                271587843661,
                953185920,
                1141440,
            ],
            "preTokenBalances": [
                {
                    "accountIndex": 1,
                    "mint": "7VUkpwzNn8s3VTgPAFESmh42aEpk5JqgUVUinSk7Tg3k",
                    "owner": "GUfCR9mK6azb9vcpsxgXyj7XRPAKJd4KMHTTVvtncGgp",
                    "uiTokenAmount": {
                        "amount": "1",
                        "decimals": 0,
                        "uiAmount": 1.0,
                        "uiAmountString": "1",
                    },
                }
            ],
            "rewards": [],
            "status": {"Ok": None},
        },
        "transaction": {
            "message": {
                "accountKeys": [
                    "H4RZVkj7H9q5Q65BMvwctJ1Fnw5f2GQyp3vVB6rnGZpx",
                    "AazL86Qi3dLpkvhTkWMW6cZCZGKz6UN1Go7RaZjdSDid",
                    "6HHrHnDEWuqDM9cgWgtdqkbwSg2Qtff4dK4At7z9qjQX",
                    "GUfCR9mK6azb9vcpsxgXyj7XRPAKJd4KMHTTVvtncGgp",
                    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                    "MEisE1HzehtrDpAAT8PnLHjpSSkRYakotTuJRPjTpo8",
                ],
                "header": {
                    "numReadonlySignedAccounts": 0,
                    "numReadonlyUnsignedAccounts": 3,
                    "numRequiredSignatures": 1,
                },
                "instructions": [
                    {
                        "accounts": [0, 1, 3, 2, 4],
                        "data": "TE6axTojnpk",
                        "programIdIndex": 5,
                    }
                ],
                "recentBlockhash": "5U5q2k1pDgeiqboFHR1UNpNEg9qzC41Pw7AJMnpHCvsT",
            },
            "signatures": [
                "2ofP3EPaGxCuizB4yFfssHHFjnFCoGzQoF3sKQotWVnsZZi24dpbDE8AVuAhjux2cYYKGBrEfnMStYqGNpTtffET"
            ],
        },
    }


class TestLambdaFunction:
    @patch("src.app.get_transaction")
    def test_lambda_handler(
        self,
        get_transaction_fn,
        kinesis_secondary_market_stream,
        kinesis_input_event: Dict[str, Any],
    ) -> None:
        get_transaction_fn.return_value = transaction_example()
        response = lambda_handler(event=kinesis_input_event, context={})

        get_transaction_fn.assert_called_once()
        assert response["message"] == "Successfully processed signature batch."

    @patch("src.app.get_transaction")
    def test_lambda_handler_when_missing_parser(
        self,
        get_transaction_fn,
        kinesis_secondary_market_stream: Generator[boto3.client, None, None],
        kinesis_invalid_input_event: Dict[str, Any],
    ) -> None:
        get_transaction_fn.return_value = transaction_example()
        response = lambda_handler(event=kinesis_invalid_input_event, context={})

        assert response["message"] == "Resulting batch is empty."
