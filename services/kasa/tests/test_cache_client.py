import json
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock
from clients.cache_client import CacheClientAsync
import uuid
import aioredis


class CacheClientTests(IsolatedAsyncioTestCase):
    def serialize(self, obj):
        return json.dumps(obj, indent=True, default=str)

    def get_redis_client(self):
        return aioredis.Redis()

    def get_cache_client(self):
        configuration = Mock()
        configuration.redis = {
            'host': 'localhost',
            'port': 6379
        }

        return CacheClientAsync(
            configuration=configuration)

    async def test_set_cache(self):
        redis = self.get_redis_client()
        client = self.get_cache_client()

        key = str(uuid.uuid4())
        value = 'helloworld'

        await client.set_cache(
            key=key,
            value=value)

        cached = await redis.get(key)
        self.assertEqual(value, cached.decode())

    async def test_set_json(self):
        redis = self.get_redis_client()
        client = self.get_cache_client()

        key = str(uuid.uuid4())
        value = {
            'message': 'helloworld'
        }

        await client.set_json(
            key=key,
            value=value)

        cached = await redis.get(key)
        result = json.loads(cached.decode())

        self.assertEqual(value, result)

    async def test_get_cache(self):
        redis = self.get_redis_client()
        client = self.get_cache_client()

        key = str(uuid.uuid4())
        value = 'helloworld'

        await redis.set(key, value.encode())

        result = await client.get_cache(
            key=key)

        self.assertEqual(result, value)

    async def test_get_json(self):
        redis = self.get_redis_client()
        client = self.get_cache_client()

        key = str(uuid.uuid4())
        data = {
            'message': 'helloworld'
        }

        value = self.serialize(data)
        await redis.set(key, value)

        result = await client.get_json(
            key=key)

        self.assertEqual(result, data)

    async def test_delete_key(self):
        redis = self.get_redis_client()
        client = self.get_cache_client()

        key = str(uuid.uuid4())
        value = 'helloworld'

        await redis.set(key, value.encode())

        write_check = await redis.get(key)
        await client.delete_key(key)
        delete_check = await redis.get(key)

        self.assertIsNotNone(write_check)
        self.assertIsNone(delete_check)

    async def test_delete_keys(self):
        redis = self.get_redis_client()
        client = self.get_cache_client()

        keys = [(str(uuid.uuid4()),
                 str(uuid.uuid4()))
                for _ in range(10)]

        all_keys = []
        for key, value in keys:
            all_keys.append(key)
            await redis.set(key, value.encode())

        write_results = []
        for key in all_keys:
            write_result = await redis.get(key)
            write_results.append(write_result)

        await client.delete_keys(all_keys)

        delete_results = []
        for key in all_keys:
            delete_result = await redis.get(key)
            delete_results.append(delete_result)

        self.assertTrue(all([x is not None for x in write_result]))
        self.assertTrue(all([x is None for x in delete_results]))
