import pytest
from data.repositories.kasa_device_repository import KasaDeviceRepository
from services.kasa_device_service import KasaDeviceService
from clients.kasa_client import KasaClient
from utils.helpers import TestData, get_mock_async_result
from unittest.mock import Mock
import unittest

from framework.testing.helpers import guid
from framework.testing.mocks import MockContainer


@pytest.mark.asyncio
class KasaDeviceServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.device_repository = Mock()
        self.kasa_client = Mock()

        container = MockContainer()

        container.define(
            KasaDeviceRepository,
            self.device_repository)

        container.define(
            KasaClient,
            self.kasa_client)

        self.service = KasaDeviceService(
            container=container)

    async def test_get_device(self):
        test_data = TestData()

        device = test_data.get_light_device()
        device_id = device.get('device_id')

        self.device_repository.get = Mock(
            return_value=get_mock_async_result(
                value=device))

        result = await self.service.get_device(
            device_id=device_id)

        self.assertIsNotNone(result)
        self.assertEqual(result.get('device_id'), device_id)

    async def test_get_all_devices(self):
        test_data = TestData()

        devices = [test_data.get_light_device() for x in range(20)]

        self.device_repository.get_all.return_value = Mock(
            return_value=get_mock_async_result(
                value=devices))

        device_ids = [x.get('device_id') for x in devices]

        result = await self.service.get_all_devices()

        self.assertIsNotNone(result)
        self.assertEqual(len(devices), len(result))
        self.assertTrue([x in result for x in device_ids])

    async def test_sync_devices(self):
        test_data = TestData()
        self.device_repository.collection = Mock()

        delete_results = Mock()
        delete_results.acknowledged = 50

        self.device_repository.collection.delete_many = Mock(
            return_value=get_mock_async_result(
                value=delete_results))

        kasa_devices = [test_data.get_kasa_light_device() for x in range(20)]
        self.kasa_client.get_devices = Mock(
            return_value=get_mock_async_result(
                value=kasa_devices))

        insert_result = Mock()
        insert_result.inserted_id = guid()

        self.device_repository.insert = Mock(
            return_value=get_mock_async_result(
                value=insert_result))

        result = await self.service.sync_devices()

        self.assertIsNotNone(result)
        self.assertEqual(20, len(result))
        self.assertEqual(20, self.device_repository.insert.call_count)
        self.assertEqual(
            1, self.device_repository.collection.delete_many.call_count)
