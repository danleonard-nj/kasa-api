from unittest.mock import AsyncMock, Mock

from clients.kasa_client import KasaClient
from data.repositories.kasa_device_repository import KasaDeviceRepository
from data.repositories.kasa_preset_repository import KasaPresetRepository
from data.repositories.kasa_scene_repository import KasaSceneRepository
from domain.exceptions import NullArgumentException
from domain.kasa.scene import KasaScene
from services.kasa_execution_service import KasaExecutionService
from tests.buildup import ApplicationBase
from framework.clients.cache_client import CacheClientAsync

from tests.helpers import TestHelper


helper = TestHelper()


def get_kasa_client(container):
    return AsyncMock()


class KasaSceneExecutionServiceTests(ApplicationBase):
    def configure_services(self, service_collection):
        service_collection.add_singleton(
            dependency_type=KasaClient,
            factory=get_kasa_client)

    async def insert_test_scene(self, **kwargs):
        repo = self.resolve(KasaSceneRepository)
        scene = helper.get_test_scene(**kwargs)
        await repo.insert(scene)

        return scene

    def get_service(self) -> KasaExecutionService:
        return self.resolve(KasaExecutionService)

    async def insert_test_preset(self, **kwargs):
        preset = helper.get_test_preset(**kwargs)
        repo = self.resolve(KasaPresetRepository)
        await repo.insert(preset)

        return preset

    async def insert_test_device(self, **kwargs):
        repo = self.resolve(KasaDeviceRepository)

        test_device = helper.get_test_device(**kwargs)
        await repo.insert(test_device)

        return test_device

    async def test_execute_scene_given_scene_calls_kasa_client_for_each_device(self):
        # Arrange
        kasa_client = self.resolve(KasaClient)
        service = self.get_service()

        test_scene_doc = await self.insert_test_scene()
        scene = KasaScene(test_scene_doc)

        all_device_ids = []
        all_preset_ids = []

        for mapping in test_scene_doc.get('mapping'):
            for device_id in mapping.get('devices'):
                await self.insert_test_device(device_id=device_id)
                all_device_ids.append(device_id)

            preset_id = mapping.get('preset_id')
            await self.insert_test_preset(preset_id=preset_id)
            all_preset_ids.append(preset_id)

        # Act
        await service.execute_scene(
            scene=scene)

        # Assert
        kasa_client.refresh_token.assert_called()

        self.assertTrue(
            kasa_client.set_device_state.call_count == len(all_device_ids))

    async def test_execute_scene_fiven_no_scene_throws(self):
        # Arrange
        service = self.get_service()

        # Act
        with self.assertRaises(NullArgumentException):
            await service.execute_scene(
                scene=None)
