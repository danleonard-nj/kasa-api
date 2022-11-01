

from utils.provider import ContainerProvider
import unittest

from framework.configuration.configuration import Configuration


class ConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        container = ContainerProvider.get_container()
        self.configuration = container.resolve(Configuration)

    def test_keyvault_configuration(self):
        self.assertIsNotNone(self.configuration.keyvault)
        self.assertIsNotNone(self.configuration.keyvault.get('vault_url'))

    def test_redis_configuration(self):
        self.assertIsNotNone(self.configuration.redis)
        self.assertIsNotNone(self.configuration.redis.get('host'))
        self.assertIsNotNone(self.configuration.redis.get('port'))

    def test_service_bus_configuration(self):
        self.assertIsNotNone(self.configuration.service_bus)
        self.assertIsNotNone(
            self.configuration.service_bus.get('connection_string'))
        self.assertIsNotNone(self.configuration.service_bus.get('queue_name'))

    def test_kasa_configuration(self):
        self.assertIsNotNone(self.configuration.kasa)
        self.assertIsNotNone(self.configuration.kasa.get('base_url'))
        self.assertIsNotNone(self.configuration.kasa.get('username'))
        self.assertIsNotNone(self.configuration.kasa.get('password'))

    def test_mongo_configuration(self):
        self.assertIsNotNone(self.configuration.mongo)
        self.assertIsNotNone(self.configuration.mongo.get('connection_string'))

    def test_azure_ad_configuration(self):
        self.assertIsNotNone(self.configuration.auth)
        self.assertIsNotNone(self.configuration.auth.get('tenant_id'))
        self.assertIsNotNone(self.configuration.auth.get('audiences'))
        self.assertIsNotNone(self.configuration.auth.get('issuer'))
        self.assertIsNotNone(self.configuration.auth.get('identity_url'))
