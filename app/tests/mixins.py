import os
import unittest
import uuid
from typing import Mapping
from unittest import mock

import boto3
import moto
import orjson
import requests

from app.tests.shared import (
    create_tables,
    cognito_create_user_pool_and_client
)
from app.web import services


class BasePatcherMixin:
    """
    For patching environment variables and a few critical AWS services.

    """

    @classmethod
    def start(cls, env_vars: Mapping, clear=False) -> dict:
        """

        Args:
            env_vars
            clear:

        Returns:
            dict: env var dictionary
        """
        cls.env_patcher = mock.patch.dict(
            os.environ,
            env_vars,
            clear=clear
        )

        cls.env_patcher.start()

        cls.mock_s3 = moto.mock_s3()
        cls.mock_dynamodb = moto.mock_dynamodb2()
        cls.mock_cognitoidp = moto.mock_cognitoidp()

        cls.mock_s3.start()
        cls.mock_dynamodb.start()
        cls.mock_cognitoidp.start()

        return os.environ

    @classmethod
    def stop(cls):
        cls.mock_cognitoidp.stop()
        cls.mock_dynamodb.stop()
        cls.mock_s3.stop()
        cls.env_patcher.stop()
        # Stop any patched properties
        if hasattr(cls, '_p_objs'):
            for k, v in cls._p_objs.items():
                for patcher in v:
                    patcher.stop()
            cls._p_objs.clear()
        # Stop any fields patch
        if hasattr(cls, '_f_objs'):
            if cls._f_objs:
                for obj_id, old_value_map in cls._f_objs.items():
                    obj = old_value_map['__self__']
                    for k, v in old_value_map.items():
                        if k != '__self__':
                            setattr(obj, k, v)
                cls._f_objs.clear()

    @classmethod
    def patch_object_properties(cls, obj_str, *args):
        if not hasattr(cls, '_p_objs'):
            cls._p_objs = {}
        cur_patched_props = []
        cur_patchers = []
        for a in args:
            patcher = mock.patch(obj_str + '.' + a, new_callable=mock.PropertyMock())
            cur_patchers.append(patcher)
            cur_patched_props.append(patcher.start())

        patchers = cls._p_objs.setdefault(obj_str, [])
        patchers.extend(cur_patchers)
        return cur_patched_props

    @classmethod
    def unpatch_object_properties(cls, obj_str, *args):
        if not hasattr(cls, '_p_objs'):
            return
        if obj_str in cls._p_objs:
            patchers = cls._p_objs[obj_str]
            for patcher in patchers:
                patcher.stop()
            del cls._p_objs[obj_str]

    @classmethod
    def patch_object_fields(cls, obj, **kwargs):
        if not hasattr(cls, '_f_objs'):
            cls._f_objs = {}
        obj_id = id(obj)
        old_value_map = cls._f_objs.setdefault(obj_id, {})
        old_value_map['__self__'] = obj
        for k, v in kwargs.items():
            old_value_map[k] = getattr(obj, k, None)
            setattr(obj, k, v)

    @classmethod
    def unpatch_object_fields(cls, obj):
        if not hasattr(cls, '_f_objs'):
            return

        obj_id = id(obj)

        old_value_map = cls._f_objs[obj_id]
        for k, v in old_value_map.items():
            if k != '__self__':
                setattr(obj, k, v)
        del cls._f_objs[obj_id]


class JsonRpcTestMixin:
    STANDARD_HEADERS = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    def jsonrpc(self, client, path, method, params, authorization=None, rid=None):
        rid = str(rid) or str(uuid.uuid1())
        resp = client.post(
            path,
            json={
                "jsonrpc": "2.0",
                "id": rid,
                "method": method,
                "params": params
            },
            headers={
                'Authorization': authorization,
                **self.STANDARD_HEADERS
            }
        )
        self.assertEqual(resp.status_code, 200)
        json_resp = resp.json()
        return json_resp.get('result'), json_resp.get('error')


class BaseTestCase(BasePatcherMixin, unittest.TestCase):
    """
    Base test case with cognito user pool and all dynamodb tables setup
    correctly via the class level setup methods.

    """

    @classmethod
    def cognito_get_public_keys(cls, user_pool_id, region):
        url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
        resp = requests.get(url)
        return resp.json()['keys']

    @classmethod
    def setUpClass(cls) -> None:
        cls.env_dict = super().start({})
        cls.env_dict['AWS_DEFAULT_REGION'] = 'us-west-2'
        cls.cognito_client = boto3.client('cognito-idp')
        cls.dynamodb_resource = boto3.resource('dynamodb')
        create_tables(cls.dynamodb_resource.meta.client)
        cls.user_pool_id, cls.user_pool_client_id = \
            cognito_create_user_pool_and_client(cls.cognito_client)
        # Update and add env vars
        cls.env_dict['COGNITO_PUBLIC_KEYS'] = orjson.dumps(
            cls.cognito_get_public_keys(
                cls.user_pool_id,
                cls.env_dict.get('AWS_REGION', 'us-west-2'),
            )
        ).decode('utf8')
        cls.env_dict['COGNITO_APP_CLIENT_ID'] = cls.user_pool_client_id
        cls.env_dict['VERIFY_TOKEN'] = '1'

        # Patch the global `user_service` instance
        cls.patch_object_fields(
            services.user_service,
            user_pool_id=cls.user_pool_id,
            user_pool_client_id=cls.user_pool_client_id,
            cognito_client=cls.cognito_client,
            dynamodb_resource=cls.dynamodb_resource
        )
        cls.patch_object_fields(
            services.user_service.user_repository,
            resource=cls.dynamodb_resource
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().stop()
