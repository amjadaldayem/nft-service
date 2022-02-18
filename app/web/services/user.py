import datetime
import logging
import time
import uuid
from typing import Optional

import orjson
from jose import jwt, jwk
from jose.utils import base64url_decode

from app.models.user import User, UserRepository
from ..exceptions import (
    AuthenticationError,
    UnknownError,
    ErrorCreatingUserInPool,
    ErrorCreatingUser,
    ErrorDeletingUserFromPool,
    DuplicateEmail,
    DuplicateUsername,
)

logger = logging.getLogger(__name__)


class PublicKeyNotFound(Exception):
    pass


class BadSignature(Exception):
    pass


class TokenExpired(Exception):
    pass


class WrongAudience(Exception):
    pass


class UserService:

    def __init__(self, *,
                 user_pool_id,
                 user_pool_client_id,
                 cognito_client,
                 dynamodb_resource):
        """
        Make suer we do _not_ do any AWS resource operations in the
        constructor. Because under test env, service instances might have been
        constructed _before_ the env vars are patched.

        Args:
            user_pool_id:
            user_pool_client_id:
            cognito_client:
            dynamodb_resource:
        """
        self.user_pool_id = user_pool_id
        self.user_pool_client_id = user_pool_client_id
        self.cognito_client = cognito_client
        self.user_repository = UserRepository(
            dynamodb_resource
        )

    def sign_up(self, email, username, password) -> User:
        if self.user_repository.get_user(email=email):
            raise DuplicateEmail(data={'details': f"Email {email} already exists."})
        if self.user_repository.get_user(nickname=username):
            raise DuplicateUsername(data={'details': f"User name {username} already exists."})

        try:
            user_data = self.cognito_client.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=email,
                TemporaryPassword=str(uuid.uuid1()),
                ForceAliasCreation=False,
                MessageAction='SUPPRESS',
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'preferred_username', 'Value': email},
                ]
            )
        except Exception as e:
            raise ErrorCreatingUserInPool(data={'details': str(e)})
        else:
            # User Id is the Sub from Cognito
            for item in user_data['User']['Attributes']:
                if item['Name'] == 'sub':
                    user_id = item['Value']
                    break
            else:
                raise UnknownError(data={'details': 'Idp does not return value sub.'})
        try:
            self.cognito_client.admin_set_user_password(
                UserPoolId=self.user_pool_id,
                Username=email,
                Permanent=True,
                Password=password
            )
        except Exception as e:
            self.cognito_delete_user(user_id)
            raise ErrorCreatingUserInPool(data={'details': str(e)})

        try:
            user = User(
                user_id=user_id,
                username=email,  # This field is used for deduping only
                preferred_username=email,
                email=email,
                nickname=username,
                joined_on=datetime.datetime.now()
            )
            self.user_repository.save_user_profile(user)
        except Exception as e:
            self.cognito_delete_user(user_id)
            raise ErrorCreatingUser(data={'details': str(e)})
        return user

    def cognito_delete_user(self, username):
        """
        Only deletes the user from the Cognito pool.

        Args:
            username:

        Returns:

        """
        try:
            self.cognito_client.admin_delete_user(
                UserPoolId=self.user_pool_id,
                Username=username
            )
        except Exception as e:
            raise ErrorDeletingUserFromPool(
                data={'details': f'Error deleting user username={username}. {str(e)}'}
            )

    def login(self, email, password):
        try:
            resp = self.cognito_client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.user_pool_client_id,
                AuthFlow='ADMIN_USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )
            result = resp['AuthenticationResult']
            access_token = result['AccessToken']
            refresh_token = result['RefreshToken']
            return access_token, refresh_token
        except Exception as e:
            raise AuthenticationError(
                data={'details': str(e)}
            )

    def get_user(self, user_id) -> Optional[User]:
        """
        TODO: Later stitch more info for the user

        Args:
            user_id:

        Returns:

        """
        return self.user_repository.get_user(user_id=user_id)

    def get_user_by_email(self, email):
        return self.user_repository.get_user(email=email)

    def extract_token(self, token, public_keys, verify=False) -> dict:
        """
        https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html

        Args:
            token:
            public_keys: A list of public key structures.
            verify: If verify the token. Set to true in the case of APIGateway we use it for authorization
                before even hitting the Lambda function.

                [
                    {
                      "alg": "RS256",
                      "e": "AQAB",
                      "kid": "Dxxq6Q...",
                      "kty": "RSA",
                      "n": "mvgEmv4c7X256BekFfjOhWxn...",
                      "use": "sig"
                    },
                ]

        Returns:
            {
              "sub": "aaaaaaaa-bbbb-cccc-dddd-example",
              "aud": "xxxxxxxxxxxxexample",
              "email_verified": true,
              "token_use": "id",
              "auth_time": 1500009400,
              "iss": "https://cognito-idp.ap-southeast-2.amazonaws.com/ap-southeast-2_example",
              "cognito:username": "anaya",
              "exp": 1500013000,
              "given_name": "Anaya",
              "iat": 1500009400,
              "email": "anaya@example.com"
            }
        """
        if not verify:
            data = str(token).split('.')[1]
            logger.info("Token: %s", str(token))
            logger.info("Splitted %s", data)
            decoded = base64url_decode(data)
            logger.info("Decoded: %s", decoded)
            return orjson.loads(decoded)
        # get the kid from the headers prior to verification
        headers = jwt.get_unverified_headers(token)
        kid = headers['kid']
        # search for the kid in the downloaded public keys
        for i, data in enumerate(public_keys):
            if kid == data['kid']:
                key_data = data
                break
        else:
            raise PublicKeyNotFound

        # construct the public key
        public_key = jwk.construct(key_data)
        # get the last two sections of the token,
        # message and signature (encoded in base64)
        message, encoded_signature = str(token).rsplit('.', 1)
        # decode the signature
        decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
        # verify the signature
        if not public_key.verify(message.encode("utf8"), decoded_signature):
            raise BadSignature
        # since we passed the verification, we can now safely
        # use the unverified claims
        claims = jwt.get_unverified_claims(token)

        if time.time() > claims['exp']:
            raise TokenExpired
        if claims['aud'] != self.user_pool_client_id:
            raise WrongAudience(f"Audience {claims['aud']} not matching client.")
        # Let's return the payload
        payload = message.split('.')[1]  # type: str
        decoded_payload = base64url_decode(payload.encode())
        return orjson.loads(decoded_payload)
