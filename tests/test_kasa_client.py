import unittest
from unittest import mock
from unittest.mock import AsyncMock, Mock

import pytest
from clients.kasa_client import KasaClient
from framework.clients.cache_client import CacheClientAsync
from framework.clients.http_client import HttpClient
from framework.configuration import Configuration
from framework.testing.helpers import guid
from framework.testing.mocks import MockContainer, MockResponse
from utils.helpers import TestData


@pytest.mark.asyncio
class KasaClientServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.cache_client: CacheClientAsync = AsyncMock()

        self.cache_service.cache_client = self.cache_client

        self.http_client: HttpClient = AsyncMock()

        self.configuration = Mock()
        self.configuration.kasa = Mock()
        self.configuration.kasa.get.return_value = guid()

        container = MockContainer()
        container.define(HttpClient, self.http_client)
        container.define(Configuration, self.configuration)

        self.service: KasaClient = KasaClient(
            container=container)

    async def test_get_devices(self):
        self.cache_client.get_cache = AsyncMock(
            return_value=None)

        self.service.__get_kasa_token = AsyncMock(
            return_value='test-token')

        test_data = TestData()
        devices = [test_data.get_kasa_light_device() for x in range(20)]

        mock_response = MockResponse(
            status_code=200,
            json={
                "error_code": 0,
                "result": {
                    "deviceList": devices
                }
            })

        self.http_client.post.return_value = mock_response
        response = await self.service.get_devices()

        self.assertIsNotNone(response)
        self.assertEqual(20, len(response.device_list))

    async def test_fetch_kasa_token_from_client(self):
        test_data = TestData()

        self.cache_client.set_cache.return_value = None
        self.cache_client.get_cache.return_value = None

        test_token = 'test_token'
        mock_response = MockResponse(
            200,
            test_data.get_kasa_client_token_response(test_token)
        )

        self.http_client.post.return_value = mock_response

        token = await self.service.__get_kasa_token()

        self.assertEqual(token, test_token)
