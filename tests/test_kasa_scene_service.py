import pytest
from data.repositories.kasa_preset_repository import KasaPresetRepository
from data.repositories.kasa_device_repository import KasaDeviceRepository
from data.repositories.kasa_scene_repository import KasaSceneRepository
from services.kasa_scene_service import KasaSceneService
from clients.kasa_client import KasaClient
from clients.service_bus import QueueClient
from domain.rest import CreateSceneRequest
from unittest.mock import Mock
import unittest


from framework.clients.cache_client import CacheClient
from framework.testing.mocks import MockContainer
from framework.testing.helpers import guid


@pytest.mark.asyncio
class KasaSceneServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        container = MockContainer()

        self.scene_repository = Mock()
        self.preset_repository = Mock()
        self.device_repository = Mock()
        self.queue_client = Mock()
        self.kasa_client = Mock()
        self.cache_client = Mock()

        container.define(
            KasaSceneRepository,
            self.scene_repository)

        container.define(
            KasaPresetRepository,
            self.preset_repository)

        container.define(
            KasaDeviceRepository,
            self.device_repository)

        container.define(
            QueueClient,
            self.queue_client)

        container.define(
            KasaClient,
            self.kasa_client)

        container.define(
            CacheClient,
            self.cache_client)

        self.service = KasaSceneService(
            container=container)

    def test_create_scene(self):
        self.scene_repository.scene_exists = Mock(
            return_value=False)

        insert_result = Mock()
        insert_result.inserted_id = guid()

        self.scene_repository.insert = Mock(
            return_value=insert_result)

        create_scene_request = CreateSceneRequest({
            'scene_name': guid(),
            'mapping': [],
            'flow': []
        })

        result = self.service.create_scene(
            request=create_scene_request)

        self.assertIsNotNone(result)
