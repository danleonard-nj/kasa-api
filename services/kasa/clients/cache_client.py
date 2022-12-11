import json
from typing import Iterable, List, Union

import aioredis
from framework.configuration.configuration import Configuration
from framework.logger.providers import get_logger
from framework.serialization.utilities import serialize

from domain.exceptions import NullArgumentException

logger = get_logger(__name__)


class CacheClientAsync:
    @property
    def client(
        self
    ) -> aioredis.Redis:
        return self.__client

    def __init__(
        self,
        configuration: Configuration
    ):
        self.__host = configuration.redis.get('host')
        self.__port = configuration.redis.get('port')

        self.__client = aioredis.Redis(
            host=self.__host,
            port=self.__port)

    async def set_cache(
        self,
        key: str,
        value: str,
        ttl=60
    ):
        '''
        Cache a string value at the specified cache key

        `key`: cache key
        `value`: cache value as `str`
        `ttl`: Cache time to live in minutes
        '''

        NullArgumentException.if_none_or_whitespace(key, 'key')
        NullArgumentException.if_none_or_whitespace(value, 'value')
        NullArgumentException.if_none(ttl, 'ttl')

        logger.info(f"Set cache key '{key}' with TTL: {ttl}")

        try:
            await self.__client.set(
                name=key,
                value=value,
                ex=(ttl * 60))

        except Exception as ex:
            logger.exception(
                f"Failed to fetch cache value at key '{key}': {str(ex)}")

    async def set_json(
        self,
        key: str,
        value: Union[dict, Iterable],
        ttl: int = 60
    ) -> None:
        '''
        Cache a serializable JSON value at the specified cache key

        `key`: cache key
        `value`: Serializable object to cache
        `ttl`: Time to live in minutes
        '''

        NullArgumentException.if_none_or_whitespace(key, 'key')
        NullArgumentException.if_none(value, 'value')
        NullArgumentException.if_none(ttl, 'ttl')

        logger.info(f"Set cache key '{key}' with TTL: {ttl}")

        await self.set_cache(
            key=key,
            value=serialize(value),
            ttl=ttl)

    async def get_cache(
        self,
        key: str
    ) -> Union[str, None]:
        '''
        Fetch a string value from cache and return value or `None` if no
        cached value exists

        `key`: cache key        
        '''

        NullArgumentException.if_none_or_whitespace(key, 'key')

        logger.info(f"Get cache value from key '{key}'")

        try:
            value = await self.__client.get(name=key)
            if value is not None:
                return value.decode()

        except Exception as ex:
            logger.exception(
                f"Failed to fetch cache value at key '{key}': {str(ex)}")

    async def get_json(
        self,
        key: str
    ) -> Union[dict, Iterable, None]:
        '''
        Fetch a serialized cache value and return the deserialized object
        or `None` if no cached value exists

        `key`: the cache key
        '''

        NullArgumentException.if_none_or_whitespace(key, 'key')

        logger.info(f"Get cache value at key '{key}'")
        value = await self.get_cache(
            key=key)

        if value is not None:
            return json.loads(value)

    async def delete_key(
        self,
        key: str
    ) -> None:
        '''
        Delete a key from the cache

        `key`: cache key
        '''

        NullArgumentException.if_none_or_whitespace(key, 'key')

        logger.info(f"Delete cache value with key '{key}'")
        await self.__client.delete(key)

    async def delete_keys(
        self,
        keys: List[str]
    ) -> None:
        '''
        Delete a key from the cache

        `key`: cache key
        '''

        NullArgumentException.if_none(keys, 'keys')

        logger.info(f"Delete cache values at keys '{keys}'")
        await self.__client.delete(*keys)
