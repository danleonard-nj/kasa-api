from unittest.mock import AsyncMock

from framework.di.service_collection import ServiceCollection

from data.repositories.kasa_preset_repository import KasaPresetRepository
from domain.rest import CreatePresetRequest
from services.kasa_preset_service import KasaPresetSevice
from tests.buildup import ApplicationBase
from tests.helpers import TestHelper

helper = TestHelper()


class KasaSceneServiceTests(ApplicationBase):
    def configure_services(self, service_collection: ServiceCollection):
        self.preset_repository = AsyncMock()

        def get_mock_preset_repository(container):
            return self.preset_repository

        service_collection.add_singleton(
            dependency_type=KasaPresetRepository,
            factory=get_mock_preset_repository)

    async def test_create_preset(self):
        # Arrange
        preset_service: KasaPresetSevice = self.resolve(
            KasaPresetSevice)

        preset_exists_by_name = self.preset_repository.preset_exists_by_name
        preset_exists_by_name.return_value = False
        insert = self.preset_repository.insert

        body = helper.get_test_create_preset_request()
        req = CreatePresetRequest(body=body)

        # Act
        await preset_service.create_preset(
            request=req)

        # Assert
        self.preset_repository.insert.assert_called()

        self.assert_kwargs(
            preset_exists_by_name,
            lambda x: x.get('preset_name') == body.get('preset_name'))
        self.assert_kwargs(
            insert,
            lambda x: x.get('document').get('preset_name') == body.get('preset_name'))
        self.assert_kwargs(
            insert,
            lambda x: x.get('document').get('device_type') == 'IOT.SMARTPLUGSWITCH')
