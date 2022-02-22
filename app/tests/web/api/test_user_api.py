import datetime
import functools
import uuid

from boto3.dynamodb.conditions import Key
from starlette.testclient import TestClient

from app.tests.mixins import JsonRpcTestMixin, BaseTestCase
from app.web import services
from app.web.api import app
from app.web.exceptions import (
    AuthenticationError,
    DuplicateEmail,
    DuplicateUsername
)


class UserAPITestCase(JsonRpcTestMixin, BaseTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    def setUp(self) -> None:
        self.client = TestClient(app)
        # Data Setup
        self.foo_nickname = 'foo'
        self.foo_email = 'foo@example.com'
        self.foo_password = 'abc123'

        self.bar_email = 'bar@example.com'
        self.bar_username = 'bar'
        self.bar_password = 'abc123456'

        self.user = services.user_service.sign_up(
            email=self.foo_email,
            nickname=self.foo_nickname,
            password=self.foo_password
        )

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
        table = self.dynamodb_resource.Table('user')
        resp = table.query(
            KeyConditionExpression=Key('pk').eq(self.user.user_id)
        )
        items = resp['Items']

    def tearDown(self) -> None:
        """
        Deletes the foo user.
        Returns:

        """
        user_id = self.user.user_id
        self.cognito_client.admin_delete_user(
            UserPoolId=self.user_pool_id,
            # Note: this will be `user_id` in real Cognito environment.
            Username=self.user.username
        )
        table = self.dynamodb_resource.Table('user')
        resp = table.query(
            KeyConditionExpression=Key('pk').eq(user_id)
        )
        items = resp['Items']
        for item in items:
            key_map = {
                'pk': item['pk'],
                'sk': item['sk']
            }
            table.delete_item(
                Key=key_map
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
