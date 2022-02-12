import dataclasses
from functools import cached_property
from typing import List, Optional, Dict

import yaml


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
                 dynamodb_resource):
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


@dataclasses.dataclass
class Attr:
    attr_name: str
    # model fields or property
    attr_value: str
    # DynamoDb datatype notation (S, N etc)
    attr_type: str = 'S'
    # class of the model, if not given, will treat `attr_value` as a literal string
    mapped_model: Optional[type] = None

    def as_hash_key_def(self):
        return {
            'AttributeName': self.attr_name,
            'KeyType': 'HASH'
        }

    def as_range_key_def(self):
        return {
            'AttributeName': self.attr_name,
            'KeyType': 'RANGE'
        }

    def as_attribute_def(self):
        return {
            'AttributeName': self.attr_name,
            'AttributeType': self.attr_type
        }


@dataclasses.dataclass
class Projection:
    # Precedence: all -> keys_only -> include
    all: bool = True
    keys_only: bool = True
    include: List[str] = dataclasses.field(default_factory=list)

    def as_projection_def(self):
        projection_type = (
            'ALL' if self.all else (
                'KEYS_ONLY' if self.keys_only else (
                    'INCLUDE'
                )
            )
        )
        ret = {
            'ProjectionType': projection_type,
        }

        if projection_type == 'INCLUDE':
            ret['NonKeyAttributes'] = self.include
        return ret


@dataclasses.dataclass
class IndexSchema:
    name: str
    gsi: bool  # True if Gsi, False for Lsi
    pk: Attr
    sk: Attr
    projection: Projection

    def as_index_def(self):
        key_schema = [
            self.pk.as_hash_key_def(),
        ]
        if self.sk:
            key_schema.append(self.sk.as_range_key_def())
        return {
            'IndexName': self.name,
            'KeySchema': key_schema,
            'Projection': self.projection.as_projection_def()
        }


@dataclasses.dataclass
class TableSchema:
    name: str
    model_classes: Dict[str, type]
    pk: Attr
    sk: Attr
    lsi_list: List[IndexSchema]
    gsi_list: List[IndexSchema]

    def get_creation_params(self) -> dict:
        """
        Generates a dictionary to feed into boto3
        dynamodb Client.create_table() method.

        Returns:

        """
        attribute_defs = {
            self.pk.attr_name: self.pk,
            self.sk.attr_name: self.sk,
        }
        for lsi in self.lsi_list:
            pk, sk = lsi.pk, lsi.sk
            attribute_defs[pk.attr_name] = pk
            if sk:
                attribute_defs[sk.attr_name] = sk

        for gsi in self.gsi_list:
            pk, sk = gsi.pk, gsi.sk
            attribute_defs[pk.attr_name] = pk
            if sk:
                attribute_defs[sk.attr_name] = sk

        attribute_defs = [
            d.as_attribute_def()
            for d in attribute_defs.values()
        ]

        key_schema = [
            self.pk.as_hash_key_def()
        ]
        if self.sk:
            key_schema.append(self.sk.as_range_key_def())

        lsi_list = [lsi.as_index_def() for lsi in self.lsi_list]
        gsi_list = [gsi.as_index_def() for gsi in self.gsi_list]

        return {
            'TableName': self.name,
            'AttributeDefinitions': attribute_defs,
            'KeySchema': key_schema,
            'LocalSecondaryIndexes': lsi_list,
            'GlobalSecondaryIndexes': gsi_list,
            'BillingMode': 'PAY_PER_REQUEST',
        }

    def create_from_api(self, client):
        """
        Note this is only used in creation of tables in testing context.
        For prod and deployed env, we use CDk (see sintra-stacks repo)

        Args:
            client:

        Returns:

        """
        client.create_table(**self.get_creation_params())
        waiter = client.get_waiter('table_exists')
        waiter.wait(
            TableName=self.name,
            WaiterConfig={
                'Delay': 5,
                'MaxAttempts': 3
            }
        )


class SchemaParser:
    table_schemas = {}

    @classmethod
    def load_schema_file(cls, file) -> Dict[str, TableSchema]:
        with open(file) as c:
            data = yaml.safe_load(c)

        for name, table_schema_dict in data.items():
            cls.table_schemas[name] = cls._parse_table_schema(table_schema_dict)

        return cls.table_schemas

    @classmethod
    def _parse_table_schema(cls, table_schema_dict) -> TableSchema:
        model_classes = {
            k: cls._load_model_class(v)
            for k, v in table_schema_dict.get('models', {}).items()
        }

        name = table_schema_dict['name']
        pk = cls._parse_attribute(table_schema_dict['pk'], model_classes)
        sk = cls._parse_attribute(table_schema_dict['sk'], model_classes)
        gsi_list = [
            cls._parse_index_schema(index_schema_dict, pk, model_classes, True)
            for index_schema_dict in table_schema_dict.get('gsi', [])
        ]
        lsi_list = [
            cls._parse_index_schema(index_schema_dict, pk, model_classes, False)
            for index_schema_dict in table_schema_dict.get('lsi', [])
        ]

        return TableSchema(
            name=name,
            model_classes=model_classes,
            pk=pk,
            sk=sk,
            gsi_list=gsi_list,
            lsi_list=lsi_list,
        )

    @classmethod
    def _parse_index_schema(cls, index_schema_dict, table_pk: Attr,
                            model_class_map: Dict[str, type], is_gsi=True) -> IndexSchema:
        name = index_schema_dict['name']
        if not is_gsi:
            pk = table_pk
        else:
            pk = cls._parse_attribute(
                index_schema_dict['pk'],
                model_class_map
            )
        sk = cls._parse_attribute(index_schema_dict['sk'], model_class_map)
        return IndexSchema(
            name=name,
            pk=pk,
            sk=sk,
            gsi=is_gsi,
            projection=cls._parse_projection(
                index_schema_dict.get('projection', {})
            )
        )

    @classmethod
    def _parse_attribute(cls, attr_dict: Optional[dict],
                         model_class_map: Dict[str, type]) -> Optional[Attr]:
        if not attr_dict:
            return None
        else:
            attr_name = attr_dict['name']
            attr_value = attr_dict['value']
            if not attr_value or not attr_name:
                raise ValueError(
                    "Empty attr_value or attr_name found."
                )
            model = None
            try:
                key, field_or_prop = attr_value.split('.')
                model = model_class_map[key]
                attr_value = field_or_prop
            except:
                pass

            return Attr(
                attr_name=attr_name,
                attr_value=attr_value,
                attr_type=attr_dict.get('attr_type', 'S'),
                mapped_model=model
            )

    @classmethod
    def _parse_projection(cls, projection_dict) -> Projection:
        """
        precendence :
            all -> keys_only -> include

        Args:
            projection_dict:

        Returns:

        """
        if not projection_dict:
            return Projection()
        all_ = projection_dict.get('all', False)
        keys_only, include = False, []
        if not all_:
            keys_only = projection_dict.get('keys_only', False)
            if not keys_only:
                include = projection_dict.get('include', [])

        return Projection(
            all=all_,
            keys_only=keys_only,
            include=include
        )

    @classmethod
    def _load_model_class(cls, class_full_name):
        package_name, class_name = class_full_name.rsplit('.', 1)
        mod = __import__(package_name, fromlist=[class_name])
        klass = getattr(mod, class_name)
        return klass
