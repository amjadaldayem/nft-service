import dataclasses
from typing import List

import orjson
from humps import camelize
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


class DataClassBase(BaseModel):
    class Config:
        extra = "ignore"
        json_loads = orjson.loads
        json_dumps = orjson_dumps
        underscore_attrs_are_private = True
        allow_population_by_field_name = True
        alias_generator = camelize


class MediaFile(DataClassBase):
    uri: str
    file_type: str = ""


class NFTCreator(DataClassBase):
    address: str
    verified: bool = False
    share: int = 0


class NFTData(DataClassBase):
    blockchain_id: int
    token_address: str
    collection_key: str
    current_owner: str
    name: str
    description: str
    symbol: str
    primary_sale_happened: bool
    metadata_uri: str
    creators: List[NFTCreator]
    ext_data: dict = dataclasses.Field(default_factory=dict)
    edition: str = ""
    attributes: dict = dataclasses.Field(default_factory=dict)
    external_url: str = ""
    files: List[MediaFile] = dataclasses.Field(default_factory=List)
