from requests import delete
from data.repositories.kasa_device_repository import KasaDeviceRepository
from domain.kasa.devices.plug import KasaPlug
from services.kasa_device_service import KasaDeviceService
from tests.buildup import ApplicationBase
from tests.helpers import TestHelper

helper = TestHelper()


class KasaDeviceServiceTests(ApplicationBase):
    async def asyncSetUp(self) -> None:
        self.repo: KasaDeviceRepository = self.provider.resolve(
            KasaDeviceRepository)
        self.service: KasaDeviceService = self.provider.resolve(
            KasaDeviceService)

    def get_mock_device(self, ):
        return KasaPlug(
            device_id=self.guid(),
            device_name=self.guid(),
            state=False)

    async def test_create_device(self):
        repo = self.provider.resolve(KasaDeviceRepository)

        device = self.get_mock_device()
        # Insert mock device
        await repo.insert(device.to_dict())

        # Get device by ID
        result = await self.service.get_device(device.device_id)

    async def test_get_device(self):
        # Create and insert test device
        device = self.get_mock_device()
        await self.repo.insert(device.to_dict())

        # Fetch inserted device
        result = await self.service.get_device(
            device_id=device.device_id)

        self.assertIsNotNone(result)

    async def test_get_device_list(self):
        device_list = await self.service.get_all_devices()

        self.assertTrue(len(device_list) > 0)
