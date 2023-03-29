from data.repositories.kasa_preset_repository import KasaPresetRepository
from domain.constants import KasaDeviceType
from domain.exceptions import PresetNotFoundException
from domain.rest import UpdatePresetRequest
from services.kasa_preset_service import KasaPresetSevice
from tests.buildup import ApplicationBase
from tests.helpers import TestHelper

helper = TestHelper()


class KasaPresetServiceTests(ApplicationBase):
    async def asyncSetUp(self) -> None:
        self.service: KasaPresetSevice = self.provider.resolve(
            KasaPresetSevice)
        self.repo: KasaPresetRepository = self.provider.resolve(
            KasaPresetRepository)

    async def test_create_preset(self):
        # Arrange
        preset_id = self.guid()

        # Create and insert test preset
        preset = helper.get_test_preset(
            preset_id=preset_id)

        await self.repo.insert(preset)

        # Act
        fetched = await self.service.get_preset(preset_id)

        # Assert
        self.assertIsNotNone(fetched)

    async def test_get_preset(self):
        # Arrange
        preset_id = self.guid()

        # Create and insert a test preset
        preset = helper.get_test_preset(
            preset_id=preset_id)

        await self.repo.insert(preset)

        # Fetch the created preset
        fetched = await self.service.get_preset(
            preset_id=preset_id)

        # Assert
        self.assertIsNotNone(fetched)

    async def test_delete_preset(self):
        # Arrange
        preset_id = self.guid()

        # Create and insert a test preset
        preset = helper.get_test_preset(
            preset_id=preset_id)

        await self.repo.insert(preset)

        # Fetch the created preset
        fetched = await self.service.get_preset(
            preset_id=preset_id)

        # Act
        # Delete the preset
        await self.service.delete_preset(
            preset_id=preset_id)

        # To confirm it's been deleted successfully as a missing
        # preset will throw
        with self.assertRaises(PresetNotFoundException):
            print('test')
            await self.service.get_preset(
                preset_id=preset_id)

        self.assertIsNotNone(fetched)

    async def test_get_presets(self):
        # Arrange
        for _ in range(10):
            preset_id = self.guid()

            # Create the dummy scenes
            preset = helper.get_test_preset(
                preset_id=preset_id)

            await self.repo.insert(preset)

        # Act
        presets = await self.service.get_all_presets()

        # Assert
        self.assertIsNotNone(presets)

    async def test_update_preset(self):
        # Arrange
        preset_id = self.guid()

        original_name = self.guid()
        updated_name = self.guid()

        # Create and insert test entity
        # to update
        preset = helper.get_test_preset(
            preset_id=preset_id,
            preset_name=original_name)

        await self.repo.insert(preset)

        # Build the preset update request
        update = UpdatePresetRequest(
            dict(
                preset_id=preset_id,
                preset_name=updated_name,
                device_type=KasaDeviceType.KasaPlug,
                definition=dict()
            )
        )

        # Act
        result = await self.service.update_preset(
            update_request=update)

        # Assert
        self.assertIsNotNone(result)
