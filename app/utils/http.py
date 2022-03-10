# Helper methods for sync and async HTTP related stuff
import orjson
from aiohttp import ClientResponse


async def get_json(response: ClientResponse):
    """
    Extracts JSON from a AIOHttp ClientResponse, regardless of MIME.
    Args:
        response:

    Returns:

    """
    """Read and decodes JSON response."""
    if response._body is None:
        await response.read()

    stripped = response._body.strip()
    if not stripped:
        return None

    encoding = response.get_encoding()

    return orjson.loads(stripped.decode(encoding))
