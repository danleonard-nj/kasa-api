import asyncio

import pytest
from data.repositories.kasa_device_repository import KasaDeviceRepository
from utils.provider import ContainerProvider
from unittest.mock import Mock
from utils.helpers import TestData, get_mock_async_result
from app import app

from framework.testing.base_api import ApiTest
from framework.testing.helpers import (
    inject_test_dependency,
    guid
)


@pytest.mark.asyncio
class DeviceTests(ApiTest):
    def setUp(self) -> None:
        super().configure(
            app=app,
            provider=ContainerProvider
        )

        self.mock_device_repository = Mock()
        inject_test_dependency(
            provider=ContainerProvider,
            _type=KasaDeviceRepository,
            instance=self.mock_device_repository)

    async def test_get_devices(self):
        builder = TestData()

        mock_devices = [builder.get_device() for x in range(10)]

        self.mock_device_repository.get_all.return_value = get_mock_async_result(
            value=mock_devices)

        result = await self.send_request(
            method='GET',
            endpoint='/api/device')

        self.assertEqual(200, result.status_code)
        self.assertIsNotNone(result.json)

    async def test_get_device(self):
        builder = TestData()
        mock_device = builder.get_device()
        mock_device_id = mock_device.get('device_id')

        self.mock_device_repository.get.return_value = get_mock_async_result(
            value=mock_device)

        result = await self.send_request(
            method='GET',
            endpoint=f'/api/device/{mock_device_id}')

        self.assertEqual(200, result.status_code)
        self.assertIsNotNone(result.json)
