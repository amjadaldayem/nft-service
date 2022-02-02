import json
from typing import Optional, Union, Any, Dict, Type

import requests
import orjson
from solana.blockhash import BlockhashCache
from solana.rpc.api import Client
from solana.rpc.commitment import Commitment
from solana.rpc.providers.http import HTTPProvider
from solana.rpc.types import RPCMethod, RPCResponse


class CustomHTTPProvider(HTTPProvider):

    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.pop("timeout", 60)
        super().__init__(*args, **kwargs)

    def make_request(self, method: RPCMethod, *params: Any) -> RPCResponse:
        """Make an HTTP request to an http rpc endpoint."""
        request_kwargs = self._before_request(method=method, params=params, is_async=False)
        raw_response = requests.post(**request_kwargs, timeout=self.timeout)
        return self._after_request(raw_response=raw_response, method=method)

    def json_decode(self, json_str: str) -> Dict[Any, Any]:  # pylint: disable=no-self-use
        """Deserialize JSON document to a Python object with friendly error messages.
        Customized with `orjson` to gain 10x speed boost on decoding.
        """
        try:
            decoded = orjson.loads(json_str)
            return decoded
        except json.decoder.JSONDecodeError as exc:
            err_msg = "Could not decode {} because of {}.".format(repr(json_str), exc)
            # Calling code may rely on catching JSONDecodeError to recognize bad json
            # so we have to re-raise the same type.
            raise json.decoder.JSONDecodeError(err_msg, exc.doc, exc.pos)


class CustomClient(Client):
    """
    A custom client with adjustable `timeout` value.
    """

    def __init__(
            self,
            endpoint: Optional[str] = None,
            commitment: Optional[Commitment] = None,
            blockhash_cache: Union[BlockhashCache, bool] = False,
            timeout: int = 30
    ) -> None:
        super().__init__(endpoint, commitment, blockhash_cache, timeout=timeout)
        # self._provider = CustomHTTPProvider(endpoint, timeout=timeout)
