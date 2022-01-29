import os
import uuid
from typing import Mapping
from unittest import mock

import moto


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
