import dataclasses
from functools import cached_property
from typing import Type, List, Optional


@dataclasses.dataclass
class MappingPair:
    table_attr_name: str
    field_name: Optional[str]
    table_attr_prefix: Optional[str] = None


class SchemaMapper:
    """
    Takes in a Dataclass and tries to map fields and properites to shorter
    format when serializing to save space.


    Python Type	                        DynamoDB Type
    string	                            String (S)
    integer	                            Number (N)
    decimal.Decimal	                    Number (N)
    boto3.dynamodb.types.Binary	        Binary (B)
    boolean	                            Boolean (BOOL)
    None	                            Null (NULL)
    string set	                        String Set (SS)
    integer set	                        Number Set (NS)
    decimal.Decimal set	                Number Set (NS)
    boto3.dynamodb.types.Binary set	    Binary Set (BS)
    list	                            List (L)
    dict	                            Map (M)
    """

    def __init__(self, facet: str,
                 dataclass: Type[dataclasses.dataclass],
                 primary_key: MappingPair,
                 sort_key: MappingPair,
                 *attr_mappings):
        self.facet = facet
        self.dataclass = dataclass
        self.primary_key = primary_key
        self.sort_key = sort_key
        self.attr_mappings = attr_mappings
        # table_attr -> (field_name, prefix) lookup
        self.lookup = {
            m.table_attr_name: (m.field_name, m.table_attr_prefix)
            for m in (self.primary_key, self.sort_key,) + self.attr_mappings
        }
        # self._generate_mappings()


class DynamoDBRepositoryBase:
    """

    """

    SNULL = ''  # Empty string

    # Constans for ReturnValues for PutItem
    RV_NONE = 'NONE'
    RV_ALL_OLD = 'ALL_OLD'
    RV_UPDATED_OLD = 'UPDATED_OLD'
    RV_ALL_NEW = 'ALL_NEW'
    RV_UPDATED_NEW = 'UPDATED_NEW'

    def __init__(self,
                 table_name,
                 dynamodb_resource,
                 schema_mapping_list: List[SchemaMapper] = None,  # TODO: imp later
                 ):
        self.table_name = table_name
        self.resource = dynamodb_resource
        # Each Facet
        # {
        #   field_name: {
        #     dynamodb_attr_name : {
        #       ''
        #     }
        #   }
        # }
        self.facets = {}
        # TODO: Later build this generic stuff
        # self._parse_schema_mapping_list(schema_mapping_list)

    @cached_property
    def table(self):
        return self.resource.Table(self.table_name)
