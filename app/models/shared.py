import copy
from typing import Union, FrozenSet, Set, Optional, Dict

import orjson
from pydantic import dataclasses


def orjson_dumps(v, *, default):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


@dataclasses.dataclass
class DataclassBase:
    # For performant (de)serialization with Fastapi / Pydantic
    class Config:
        extra = 'ignore'
        json_loads = orjson.loads
        json_dumps = orjson_dumps
        underscore_attrs_are_private = True
