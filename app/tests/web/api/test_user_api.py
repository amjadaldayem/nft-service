import datetime
import functools
import unittest
import uuid
from typing import Union

import boto3
import orjson
import requests
from starlette.testclient import TestClient

from app.models import User
from app.tests.mixins import BasePatcherMixin, JsonRpcTestMixin
from app.tests.shared import create_tables
from app.web import services
from app.web.api import app
from app.web.exceptions import (
    AuthenticationError,
    DuplicateEmail,
    DuplicateUsername
)


class TestUserAPI(JsonRpcTestMixin, BasePatcherMixin, unittest.TestCase):

    @classmethod
    def cognito_get_public_keys(cls, user_pool_id, region):
        url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
        resp = requests.get(url)
        return resp.json()['keys']

    @classmethod
    def cognito_create_user_pool_and_client(cls, cognito_client) -> Union[str, str]:
        user_pool_creation_args = {
            'Policies': {
                'PasswordPolicy': {
                    'MinimumLength': 6,
                    'RequireNumbers': True
                }
            },
            'PoolName': 'test-user-pool',
            'AdminCreateUserConfig': {
                'AllowAdminCreateUserOnly': True
            },
            'AutoVerifiedAttributes': [
                'email',
            ],
            'AliasAttributes': [
                'phone_number',
                'email',
                'preferred_username'
            ],
            'Schema': [
                {
                    'Name': 'email',
                    'Required': True,
                    'Mutable': True,
                    'AttributeDataType': 'String'
                },
                {
                    'Name': 'preferred_username',
                    'Required': True,
                    'Mutable': True,
                    'AttributeDataType': 'String'
                },
                {
                    'Name': 'phone_number',
                    'Required': False,
                    'Mutable': True,
                    'AttributeDataType': 'String'
                },
                {
                    'Name': 'joined_on',
                    'Required': False,
                    'Mutable': False,
                    'AttributeDataType': 'DateTime'
                }
            ],
        }
        user_pool = cognito_client.create_user_pool(
            **user_pool_creation_args
        )['UserPool']
        user_pool_id = user_pool['Id']
        user_pool_client = cognito_client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName='test-user-pool-client',
        )['UserPoolClient']
        return user_pool_id, user_pool_client['ClientId']

    @classmethod
    def setUpClass(cls) -> None:
        cls.env_dict = super().start({})
        cls.env_dict['AWS_DEFAULT_REGION'] = 'us-west-2'
        cls.cognito_client = boto3.client('cognito-idp')
        cls.dynamodb_resource = boto3.resource('dynamodb')
        create_tables(cls.dynamodb_resource.meta.client)
        cls.user_pool_id, cls.user_pool_client_id = \
            cls.cognito_create_user_pool_and_client(cls.cognito_client)

        # Update and add env vars
        cls.env_dict['COGNITO_PUBLIC_KEYS'] = orjson.dumps(
            cls.cognito_get_public_keys(
                cls.user_pool_id,
                cls.env_dict.get('AWS_REGION', 'us-west-2'),
            )
        ).decode('utf8')
        cls.env_dict['COGNITO_APP_CLIENT_ID'] = cls.user_pool_client_id
        cls.env_dict['VERIFY_TOKEN'] = '1'

        # Creates DynamoDb table

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
        cls.foo_nickname = 'foo'
        cls.foo_email = 'foo@example.com'
        cls.foo_password = 'abc123'

        cls.bar_email = 'bar@example.com'
        cls.bar_username = 'bar'
        cls.bar_password = 'abc123456'

        cls.user = services.user_service.sign_up(
            email=cls.foo_email,
            nickname=cls.foo_nickname,
            password=cls.foo_password
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().stop()

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.rpc = functools.partial(
            self.jsonrpc,
            self.client,
            path='/v1/rpc'
        )
        self._rpc = functools.partial(
            self.jsonrpc,
            self.client,
            path='/v1/_rpc'
        )

    def test_non_existent_paths(self):
        resp = self.client.get('/123')
        self.assertEqual(resp.status_code, 404)

    def test_non_existent_methods(self):
        result, error = self.rpc(method='not-a-method', params={})
        self.assertIsNone(result)
        # Method not found.
        self.assertEqual(error['code'], -32601)

    def test_get_revision(self):
        result, error = self.rpc(
            method='getRevision',
            params={}
        )
        self.assertIsNone(error)
        self.assertIn('NONE', result)

    def test_echo_authenticated(self):
        auth, _ = services.user_service.login(
            self.foo_email, self.foo_password
        )
        result, error = self._rpc(
            method='echo',
            params={'data': 123},
            authorization=auth
        )
        self.assertIsNotNone(result)

    def test_echo_not_authenticated(self):
        result, error = self._rpc(
            method='echo',
            params={'data': 123}
        )
        self.assertIsNone(result)
        self.assertEqual(error['code'], AuthenticationError.CODE)

    def test_sign_up(self):
        result, error = self.rpc(
            method='signUp',
            params={
                'data': {
                    'email': self.bar_email,
                    'nickname': self.bar_username,
                    'password': self.bar_password
                }
            }
        )
        self.assertIsNone(error)
        user_id = result['userId']
        readback = services.user_service.get_user(user_id)
        result['joinedOn'] = datetime.datetime.fromisoformat(result['joinedOn'])

        self.assertEqual(
            readback.dict(by_alias=True),
            result
        )

    def test_sign_up_bad_username(self):
        result, error = self.rpc(
            method='signUp',
            params={
                'data': {
                    'email': "a@a.com",
                    'nickname': "1",
                    'password': "abc12345"
                }
            }
        )
        self.assertIsNotNone(error)
        self.assertEqual(error['code'], -32602)
        result, error = self.rpc(
            method='signUp',
            params={
                'data': {
                    'email': "a@a.com",
                    'nickname': "a" * 99,
                    'password': "abc12345"
                }
            }
        )
        self.assertIsNotNone(error)
        self.assertEqual(error['code'], -32602)

    def test_sign_up_bad_email(self):
        result, error = self.rpc(
            method='signUp',
            params={
                'data': {
                    'email': "not-valid-email",
                    'nickname': "qfasdfdF",
                    'password': "abc12345"
                }
            }
        )
        self.assertIsNotNone(error)
        self.assertEqual(error['code'], -32602)

    def test_sign_up_with_dupe_email(self):
        result, error = self.rpc(
            method='signUp',
            params={
                'data': {
                    'email': self.foo_email,
                    'nickname': str(uuid.uuid4()),
                    'password': "abc12345"
                }
            }
        )
        self.assertIsNotNone(error)
        self.assertEqual(error['code'], DuplicateEmail.CODE)

    def test_sign_up_with_dupe_username(self):
        result, error = self.rpc(
            method='signUp',
            params={
                'data': {
                    'email': str(uuid.uuid4()) + "@example.com",
                    'nickname': self.foo_nickname,
                    'password': "abc12345"
                }
            }
        )
        self.assertIsNotNone(error)
        self.assertEqual(error['code'], DuplicateUsername.CODE)

    def test_login(self):
        result, error = self.rpc(
            method='login',
            params={
                'data': {
                    'email': self.foo_email,
                    'password': self.foo_password
                }
            },
        )
        self.assertIsNone(error)
        auth = result['accessToken']
        result, error = self._rpc(
            method='getUserData',
            params={},
            authorization=auth
        )
        self.assertIsNone(error)
        self.assertEqual(
            result['nickname'],
            self.foo_nickname
        )
        self.assertEqual(
            result['email'],
            self.foo_email
        )

    def test_get_user_data(self):
        auth, _ = services.user_service.login(
            self.foo_email, self.foo_password
        )
        result, error = self._rpc(
            method='getUserData',
            params={},
            authorization=auth
        )
        self.assertIsNone(error)
        self.assertEqual(
            result['nickname'],
            self.foo_nickname
        )
