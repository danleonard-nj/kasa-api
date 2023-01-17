import os
import unittest
import uuid
from abc import abstractmethod
from unittest.mock import AsyncMock, Mock

from framework.clients import CacheClientAsync
from framework.di.service_provider import ServiceCollection, ServiceProvider
from framework.logger import get_logger
from motor.motor_asyncio import AsyncIOMotorClient

from utils.provider import ContainerProvider

logger = get_logger(__name__)

REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'


def get_mongo_cnxn():
    mongo_host = os.environ.get('MONGO_HOST') or 'localhost'
    mongo_port = os.environ.get('LOCAL_MONGO_PORT_OVERRIDE', 27017)

    mongo_cnxn = f'mongodb://{mongo_host}:{mongo_port}'
    logger.info(f'Mongo: {mongo_cnxn}')

    return mongo_cnxn


def configure_test_client(container):
    client = AsyncIOMotorClient(get_mongo_cnxn())
    return client


def configure_test_redis(container):
    mock = AsyncMock()
    mock.get_json.return_value = None
    return mock


class ApplicationBase(unittest.IsolatedAsyncioTestCase):
    def get_provider(self) -> ServiceProvider:
        return self.provider

    def resolve(self, _type):
        return self.provider.resolve(_type)

    def guid(self):
        return str(uuid.uuid4())

    @abstractmethod
    def configure_services(self, service_collection: ServiceCollection):
        pass

    def setUp(self):
        services = ContainerProvider.configure_container()
        services.add_singleton(
            dependency_type=AsyncIOMotorClient,
            factory=configure_test_client)

        services.add_singleton(
            dependency_type=CacheClientAsync,
            factory=configure_test_redis)

        self.configure_services(
            service_collection=services)

        provider = ServiceProvider(
            service_collection=services)
        provider.build()

        self.provider = provider
