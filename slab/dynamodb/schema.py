from abc import ABC
from enum import Enum
from typing import List, Type, Tuple, Dict, Optional

import boto3
from pydantic import BaseModel


class InvalidSchema(Exception):
    pass


class DataType(str, Enum):
    """
    Mapping of DynamoDB Data Types
    """
    String = 'S'
    Number = 'N'
    Boolean = 'BOOL'
    Binary = 'B'
    Date = 'S'
    StringSet = 'SS'
    NumberSet = 'NS'
    BinarySet = 'BS'


class ProjectType(str, Enum):
    ALL = 'ALL'
    KEYS_ONLY = 'KEYS_ONLY'


class GSIDecl(BaseModel):
    name: str
    partition_key: Tuple[str, DataType]
    sort_key: Optional[Tuple[str, DataType]] = None
    projection: ProjectType


class ModelDecl(BaseModel):
    name: str
    partition_key: Tuple[str, DataType]
    sort_key: Optional[Tuple[str, DataType]] = None
    gsi_list: List[Dict] = []


class StdSchemaDefinition:
    """
    Abstract Base Class for implementing Single Table Design

    https://aws.amazon.com/blogs/compute/creating-a-single-table-design-with-amazon-dynamodb/

    """
    name: str = None
    billing_mode = 'PAY_PER_REQUEST'
    table_class = 'STANDARD'
    models: List[dict] = []


def create_table(schema: StdSchemaDefinition, resource=None):
    """

    Args:
        schema:
        resource:

    Returns:

    """
    table_name = schema.name
    if not table_name or len(table_name) < 2:
        raise InvalidSchema("The `name` field cannot be None or less than 2 characters.")

    attribute_definitions = []
    gsis = []
    all_index_names = set()
    for model_dict in schema.models:
        try:
            model_decl = ModelDecl(model_dict)
            for gsi_dict in model_decl.gsi_list:
                gsi_decl = GSIDecl(gsi_dict)
                index_name = model_decl.name + '_' + gsi_decl.name
                if index_name not in all_index_names:
                    all_index_names.add(index_name)
                else:
                    raise InvalidSchema(
                        f"Duplicate index name `{index_name}` under the "
                        f"same model {model_decl.name}"
                    )
                # TODO: Finish this
                key_schema = [
                    {

                    }
                ]
                if gsi_decl.sort_key:
                    key_schema.append(
                        {

                        }
                    )

                gsis.append({
                    'IndexName': index_name,
                    'KeySchema': key_schema,
                })
        except Exception:
            raise

    # Blocking operation.
    args = {}
    resource = resource or boto3.resource('dynamodb')
    client = resource.meta.client
    client.create_table(**args)
    table = resource.Table(table_name)
    table.wait_until_exists()
    return table
