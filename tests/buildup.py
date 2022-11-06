import unittest
import uuid
from unittest.mock import Mock

from framework.clients import CacheClientAsync
from framework.di.service_provider import ServiceProvider
from motor.motor_asyncio import AsyncIOMotorClient

from utils.provider import ContainerProvider
import os

REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
MONGO_HOST = os.environ.get('MONGO_HOST') or 'localhost'


def configure_test_client(container):
    client = AsyncIOMotorClient(F'mongodb://{MONGO_HOST}:27017')
    return client


def configure_test_redis(container):
    configuration = Mock()
    configuration.redis = {
        'host': REDIS_HOST,
        'port': '6379'
    }

    cache_client = CacheClientAsync(
        configuration=configuration)

    return cache_client


class ApplicationBase(unittest.IsolatedAsyncioTestCase):
    def get_provider(self) -> ServiceProvider:
        return self.provider

    def resolve(self, _type):
        return self.provider.resolve(_type)

    def guid(self):
        return str(uuid.uuid4())

    def setUp(self):
        services = ContainerProvider.configure_container()
        services.add_singleton(
            dependency_type=AsyncIOMotorClient,
            factory=configure_test_client)

        services.add_singleton(
            dependency_type=CacheClientAsync,
            factory=configure_test_redis)

        provider = ServiceProvider(
            service_collection=services)
        provider.build()

        self.provider = provider
