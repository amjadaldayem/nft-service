# -*- coding: utf-8 -*-
# Module:    db
import logging
import os
import hashlib

import boto3
from boto3.dynamodb import conditions
from boto3.dynamodb.conditions import Key

from mrs.common.dynamo_reserved_words import RESERVED_WORDS
from mrs.exceptions import DataStoreError, DynamoDBValidationError

from mrs import settings


logger = logging.getLogger(__name__)


def flatten_secondary_indexes(global_secondary_indexes):
    """ Return a flattened list of all secondary indexes attribute names.
    Args:
        global_secondary_indexes (list/tuple of list/tuple of str):
            List of List containing either Partition Key and Sort Key OR
            just Partition Key. e.g. [('status',), ['design_pk', 'img_url']]
    Returns:
        Flat list of attribute names, e.g. ['status', 'design_pk', 'img_url']
    """
    attributes = {index for secondary_indexes in global_secondary_indexes
                  for index in secondary_indexes}
    return list(attributes)


def check_for_reserved_words(attr, value=None):
    """
        Check args for reserved words and update with workaround.

    Args:
        attr (str): attribute to check if reserved
        value (object): accompanying value to also update

    Returns:

    """
    if attr in RESERVED_WORDS:
        attr_name = "#{}".format(attr)
        attr_value = None
        if value is not None:
            h = hashlib.sha1(str(value)).hexdigest()
            attr_value = ":{}".format(h)
        return True, attr_name, attr_value
    else:
        return False, attr, value


class DynamoDB(object):
    """ DynamoDB interface (create Tables, CRUD Table Items) """
    _table = None

    def __init__(self, table_name, attributes, attribute_types, partition_key,
                 sort_key=None, global_secondary_indexes=None):
        """ Initialize DynamoDB resource

        Args:
            table_name (str): DynamoDB Table name
            attributes (list): Item attribute names
            attribute_types (dict): Mapping between
                                      field name -> DynamoDB Data Types
            partition_key (str): DynamoDB Partition Key (Primary Key)
            sort_key (str, optional): DynamoDB Sort Key,
                (Sort Key + Partition Key == Composite Primary Key)
            global_secondary_indexes (iterable, optional): list/tuple of str,
                (Partition Key) OR (Partition Key, Sort Key)
        """
        self.table_name = table_name
        self.attributes = attributes
        self.attribute_types = attribute_types
        self.partition_key = partition_key
        self.sort_key = sort_key
        self.global_secondary_indexes = global_secondary_indexes
        # set endpoint url if `DYNAMODB_ENDPOINT` in env
        dynamo_url = os.getenv('DYNAMODB_ENDPOINT')
        endpoint_kwargs = {'endpoint_url': dynamo_url} if dynamo_url else {}
        self.resource = boto3.resource('dynamodb', **endpoint_kwargs)
        self.client = self.resource.meta.client

    def _get_attribute_definitions(self):
        """ Return a list of dicts describing the key schema for the table and
        indexes. Each of these dicts will contain:
            `AttributeName` (str): A name for the attribute.
            `AttributeType` (str): The data type for the attribute
                                   ('S' | 'N' | 'B')
        """
        attribute_type = self.attribute_types[self.partition_key]
        definitions = [{'AttributeName': self.partition_key,
                        'AttributeType': attribute_type}]
        for gsi in flatten_secondary_indexes(
                self.global_secondary_indexes):
            attribute_type = self.attribute_types[gsi]
            definitions.append({
                'AttributeName': gsi,
                'AttributeType': attribute_type
            })
        return definitions

    def _get_table_schema(self):
        """ Return a list of Primary Key Attribute(s) mappings for the table.
        Each mapping will have:
            `AttributeName` (str): Attribute Name
            `KeyType` (str): Partition Key ('HASH') or Sort Key ('Range')
        """
        schema = [{'AttributeName': self.partition_key, 'KeyType': 'HASH'}]
        if self.sort_key:
            schema.append({'AttributeName': self.sort_key, 'KeyType': 'RANGE'})
        return schema

    def _get_global_secondary_indexes(self):
        """ Return Secondary Global Indexes for the table.  """
        indexes = []
        if len(self.global_secondary_indexes) > 5:
            raise DynamoDBValidationError(
                'You can have at most 5 Global Secondary Indexes.'
            )
        for global_secondary_index in self.global_secondary_indexes:
            index_length = len(global_secondary_index)

            if index_length < 1 or index_length > 2:
                raise DynamoDBValidationError(
                    'Global Secondary Indexes must either have: '
                    'A Partition Key *OR* a Partition Key + a Sort Key.')

            index_partition_key = global_secondary_index[0]
            index = {
                'IndexName': index_partition_key,
                'KeySchema': [
                    {
                        'AttributeName': index_partition_key,
                        'KeyType': 'HASH'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 4,
                    'WriteCapacityUnits': 3
                }
            }

            if index_length == 2:
                index_sort_key = global_secondary_index[1]
                index['KeySchema'].append({
                    'AttributeName': index_sort_key,
                    'KeyType': 'RANGE'
                })

            indexes.append(index)
        return indexes

    def create_table(self):
        """ Idempotent, create a table if it doesn't exist using current
        DataStore partition_key, sort_key and global_secondary_indexes.

        Returns: Active dynamodb.Table
        """
        table_kwargs = {
            'TableName': self.table_name,
            'AttributeDefinitions': self._get_attribute_definitions(),
            'KeySchema': self._get_table_schema(),
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 4,
                'WriteCapacityUnits': 3
            }
        }

        if self.global_secondary_indexes:
            table_kwargs['GlobalSecondaryIndexes'] = \
                self._get_global_secondary_indexes()

        logger.info("Creating table %s.", self.table_name)
        logger.debug("Table kwargs: %s", table_kwargs)
        try:
            self.resource.create_table(**table_kwargs)
        except self.client.exceptions.ResourceInUseException:
            pass
        except Exception:
            raise
        return self.get_table()

    def _delete_table(self):
        """ Delete Table. """
        table = self.get_table()
        table.delete()

    def get_table(self):
        """ Get DynamoDB Table Resource once the Table is in ACTIVE state.
        Cache the Table. Create one if not exists.
        """
        if not self._table:
            waiter = self.client.get_waiter('table_exists')
            waiter.wait(
                TableName=self.table_name,
                WaiterConfig={
                    'Delay': 20,
                    'MaxAttempts': 15
                }
            )
            self._table = self.resource.Table(self.table_name)
        return self._table

    def get_item(self, partition_key_value, sort_key_value=None,
                 consistent_read=True, attributes=None):
        """ Get an Item from a DynamoDB Table

        Args:
            partition_key_value (str): Partition Key value we're looking for
            sort_key_value (str, optional): If present, Sort Key value
            consistent_read (bool, optional): Consistent Read
            attributes (list of str | None): Which attributes should we get?

        Returns:
            dict | None: Returns the Item dict or None if not exists.
        """
        keys = {self.partition_key: partition_key_value}

        if sort_key_value:
            keys[self.sort_key] = sort_key_value

        item_kwargs = {
            'Key': keys,
            'ConsistentRead': consistent_read,
            'ReturnConsumedCapacity': 'NONE'
        }
        if attributes:
            if any(attr not in self.attributes for attr in attributes):
                raise DynamoDBValidationError('Partition Key is Required.')
            item_kwargs['AttributesToGet'] = attributes
        table = self.get_table()
        response = table.get_item(**item_kwargs)
        return response.get('Item')

    def get_items(self, item_pks):
        """ Get a Batch of items with Partition Key in `item_pks`
        Args:
            item_pks (list): Partition Keys list

        Returns:
        """
        # FIXME: I might be broken
        items = []
        for item_pk in item_pks:
            items.append({
                self.partition_key: item_pk
            })

        response = self.client.batch_get_item(
            RequestItems={
                self.table_name: {
                    'Keys': items
                }
            }
        )
        # TODO: handle UnprocessedKeys
        return response.get('Responses', {}).get(self.table_name, [])

    def create_item(self, **kwargs):
        """ Gets a keyword arguments and creates an Item in DyanamoDB.

        Args:
            kwargs (dict): key - values
        Returns:
            None if all is good
        Raises:
            Probably raises something when all is not good
        """
        item_attributes = kwargs.keys()
        if self.partition_key not in item_attributes:
            raise DynamoDBValidationError('Partition Key is Required.')
        if self.sort_key and self.sort_key not in item_attributes:
            raise DynamoDBValidationError('Sort Key is Required.')
        table = self.get_table()
        table.put_item(
            Item=kwargs,
            ConditionExpression=conditions.Attr(
                self.partition_key
            ).not_exists()
        )

    def update_item(self, partition_key_value, sort_key_value=None, **kwargs):
        """ Updates item with primary key `partition_key_value` and
        (optionally) sort key `sort_key_value` with `kwargs` keywords mappings.

        Args:
            partition_key_value (str): partition key value of the item
                to be updated
            sort_key_value (str, optional): sort key value if present
            kwargs (dict): mapping from attribute names to values to be updated
        """
        keys = {self.partition_key: partition_key_value}
        if sort_key_value:
            keys[self.sort_key] = sort_key_value

        attribute_names = {}
        attribute_values = {}
        set_pairs = []
        for attribute, value in kwargs.items():
            reserved, attr_name, attr_value = check_for_reserved_words(
                attribute, value=value)
            if reserved:
                attribute_names.update({attr_name: attribute})
                attribute_values.update({attr_value: value})
                set_pairs.append('{0} = {1}'.format(attr_name, attr_value))
            else:
                attribute_values.update({':{0}'.format(attribute): value})
                set_pairs.append('{0} = :{0}'.format(attribute))

        update_expression = 'SET {0}'.format(', '.join(set_pairs))

        attribute_name_kwargs = {}
        if attribute_names:
            attribute_name_kwargs['ExpressionAttributeNames'] = attribute_names

        # TODO: lock updates, check dynamobdlock on how to do this
        #   (avoid race conditions from multiple concurrent updates)

        table = self.get_table()

        table.update_item(
            Key=keys,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=attribute_values,
            **attribute_name_kwargs
        )

    def query(self, key, key_value, limit=None, fields=None,
              scan_index_forward=True):
        """
        Query table for items where key == key_value
        Args:
            key (str): must be an index
            key_value (object):
            limit (int):
            fields (list): a list of fields to return
            scan_index_forward (bool): True for asc sort order, False for desc

        Returns:

        """
        query_kwargs = {
            'TableName': self.table_name,
            'IndexName': key,
            'KeyConditionExpression': Key(key).eq(key_value)
        }

        if limit:
            query_kwargs['Limit'] = limit

        expr_attr_names = {}
        for i, field in enumerate(fields):
            reserved, new_field, _ = check_for_reserved_words(field)
            if reserved:
                fields[i] = new_field
                expr_attr_names[new_field] = field

        if expr_attr_names:
            query_kwargs['ExpressionAttributeNames'] = expr_attr_names

        if fields:
            query_kwargs['ProjectionExpression'] = ', '.join(fields)

        if scan_index_forward:
            query_kwargs['ScanIndexForward'] = scan_index_forward

        response = self.client.query(
            **query_kwargs
        )

        return response.get('Items')

    def query_raw(self, index_name, cond, attrs_to_return,
                  limit,
                  reverse=False,
                  exclusive_start_key=None,
                  ):
        """
        The powerful paginated query.
        Args:
            index_name (str):
            cond (:obj:`list` of
                :obj:`boto3.dynamodb.conditions.ConditionBase`):
            attrs_to_return (:obj:`list` of :obj:`str`):
            limit (int)
            reverse (bool): If returns value in reverse order or not.
            exclusive_start_key (str | int | None):

        Returns:
            list, int, str|None: List of items, total count,
                exclusive_start_key or None
        """
        table = self.get_table()

        attr_keys = ['#I' + str(c) for c in range(len(attrs_to_return))]
        attr_names = dict(zip(attr_keys, attrs_to_return))

        kwargs = {
            'IndexName': index_name,
            'Limit': limit,
            'ConsistentRead': False,
            'ScanIndexForward': not reverse,
            'KeyConditionExpression': cond,
            'ProjectionExpression': ','.join(attr_keys),
            'ExpressionAttributeNames': attr_names,
        }
        if exclusive_start_key:
            kwargs['ExclusiveStartKey'] = exclusive_start_key

        ret = table.query(**kwargs)

        return ret['Items'], ret['Count'], ret.get('LastEvaluatedKey')

    def batch_get_items(self, keys, values_to_return, chunk_size=100):
        keys = list(keys)
        if not keys:
            return []
        if chunk_size <= 0:
            # If we still have keys but chunk_size shrank to <=1,
            # we are in trouble
            logger.error(
                "Not able to retrieve all items requested keys = %",
                keys
            )
            return []
        total = len(keys)
        result = []
        retrying_keys = []
        for x in range(0, total, chunk_size):
            chunk_keys = keys[x:x + chunk_size]
            if chunk_keys:
                items, unprocessed = self._batch_get_items(
                    chunk_keys, values_to_return
                )
                result.extend(items)
                if unprocessed:
                    retrying_keys.extend(unprocessed)
        # Retries
        if retrying_keys:
            # Maximum retries
            result.extend(
                self.batch_get_items(
                    retrying_keys,
                    values_to_return,
                    chunk_size=int(chunk_size / 2)
                )
            )
        return result

    def _batch_get_items(self, keys, values_to_return):
        """
        Assuming the partition key name is 'id'
        Args:
            keys:
            values_to_return:

        Returns:

        """
        kwargs = {
            'Keys': [{'id': v} for v in keys],
            'ConsistentRead': True,
        }
        if values_to_return:
            attr_keys = ['#I' + str(c) for c in range(len(values_to_return))]
            attr_names = dict(zip(attr_keys, values_to_return))
            kwargs.update({
                'ProjectionExpression': ','.join(attr_keys),
                'ExpressionAttributeNames': attr_names,
            })

        resp = self.client.batch_get_item(
            RequestItems={
                self.table_name: kwargs
            },
            ReturnConsumedCapacity='NONE'
        )
        items = resp.get('Responses', {}).get(self.table_name, [])
        unprocessed_keys = resp.get('UnprocessedKeys', {}).\
            get(self.table_name, {}).get('Keys', [])
        return items, unprocessed_keys

    def batch_write_items(self, items):
        table = self.get_table()
        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)


class DynamoDBDataStore(object):

    def __init__(self, model_class):
        """ Introspect a Model, get from it what we need to create a
        DynamoDB interface, and create it.
        Args:
            model_class (obj): mrs.common.Model class
        """
        self.model_class = model_class
        self.model_class_meta = getattr(self.model_class, 'Meta', None)
        self.table_name = self.get_table_name()
        self.partition_key = self.model_class.get_partition_key()
        self.sort_key = self.model_class.get_sort_key()
        self.global_secondary_indexes = getattr(
            self.model_class_meta, 'global_secondary_indexes', [])
        flattened_secondary_indexes = flatten_secondary_indexes(
            self.global_secondary_indexes)
        self.attribute_types = self.get_attribute_types(
            self.partition_key, *flattened_secondary_indexes)
        self._dynamodb = DynamoDB(
            table_name=self.table_name, partition_key=self.partition_key,
            sort_key=self.sort_key,
            global_secondary_indexes=self.global_secondary_indexes,
            attribute_types=self.attribute_types,
            attributes=self.model_class.fields.keys())

    def __getattr__(self, name):
        """ Delegate to DynamoDB Interface public methods
        Args:
            name (str): method name
        """
        def wrapper(*args, **kwargs):
            if not name.startswith('_') and hasattr(self._dynamodb, name):
                attr = getattr(self._dynamodb, name)
                if callable(attr):
                    return attr(*args, **kwargs)
            raise AttributeError("'DynamoDBDataStore' object has"
                                 " no attribute '{0}'".format(name))
        return wrapper

    def get_table_name(self):
        """ Get DynamoDB Table name from Model. If set in Meta class,
        use `db_table` attribute, else, use the Model class name.
        Returns:
            A str for the table name
        """
        if self.model_class_meta and hasattr(self.model_class_meta,
                                             'db_table'):
            table_name = self.model_class_meta.db_table
        else:
            table_name = self.model_class.__name__

        table_name = '{0}-mrs-{1}'.format(settings.DEPLOYMENT_ENV,
                                          table_name.lower())
        return table_name

    @staticmethod
    def _get_type_from_primitive(field):
        """ Get a Schematics Field and return a DynamoDB data type.
        Args:
            field: A type field from schematics.types.
        Returns:
            A str representing a DynamoDB Data Type.

        """
        if field.primitive_type is str:
            return 'S'
        elif field.primitive_type is unicode:
            return 'S'
        elif field.primitive_type is int:
            return 'N'
        elif field.primitive_type is float:
            return 'N'
        else:
            raise DataStoreError('Primitive to Data Type Mapping not found.')

    def get_attribute_types(self, *field_names):
        """ Introspect Model attribute types for some of its fields, and map
        Model field names to DynamoDB Data Types.
        Args:
            field_names (list of str): Model field names we want
                DynamoDB Data Types for
        Returns:
            A dict with <field_name> keys, <dynamodb_data_type> values
        """
        return {
            field_name: self._get_type_from_primitive(field_type)
            for (field_name, field_type) in self.model_class.fields.items()
            if field_name in field_names
        }
