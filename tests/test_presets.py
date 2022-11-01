import pytest
from data.repositories.kasa_preset_repository import KasaPresetRepository
from utils.provider import ContainerProvider
from utils.helpers import TestData, get_mock_async_result
from unittest.mock import Mock
from app import app

from framework.testing.helpers import inject_test_dependency, guid
from framework.testing.base_api import ApiTest


@pytest.mark.asyncio
class PresetTests(ApiTest):
    def setUp(self) -> None:
        super().configure(
            app=app,
            provider=ContainerProvider)

        self.mock_preset_repository = Mock()

        inject_test_dependency(
            provider=ContainerProvider,
            _type=KasaPresetRepository,
            instance=self.mock_preset_repository)

    async def test_get_presets(self):
        builder = TestData()
        mock_presets = [builder.get_preset() for x in range(10)]

        self.mock_preset_repository.get_all.return_value = get_mock_async_result(
            value=mock_presets)

        result = await self.send_request(
            method='GET',
            endpoint='/api/preset')

        self.assertEqual(200, result.status_code)
        self.assertIsNotNone(result.json)

    async def test_get_preset(self):
        builder = TestData()
        mock_preset = builder.get_preset()
        mock_preset_id = mock_preset.get('preset_id')

        self.mock_preset_repository.get.return_value = get_mock_async_result(
            value=mock_preset)

        result = self.send_request(
            method='GET',
            endpoint=f'/api/preset/{mock_preset_id}')

        self.assertEqual(200, result.status_code)
        self.assertIsNotNone(result.json)

    async def test_delete_preset(self):
        builder = TestData()

        mock_preset = builder.get_preset()
        mock_preset_id = mock_preset.get('preset_id')

        self.mock_preset_repository.get.return_value = mock_preset
        self.mock_preset_repository.delete.return_value = builder.get_delete_result(
            deleted_count=1)

        result = self.send_request(
            method='DELETE',
            endpoint=f'/api/preset/{mock_preset_id}')

        self.assertEqual(200, result.status_code)
        self.assertIsNotNone(result.json)

    async def test_create_preset(self):
        builder = TestData()

        mock_preset = builder.get_preset()

        mock_insert = Mock()
        mock_insert.inserted_id = guid()

        self.mock_preset_repository.preset_exists.return_value = get_mock_async_result(
            value=False)
        self.mock_preset_repository.insert.return_value = get_mock_async_result(
            value=mock_insert)

        result = await self.send_request(
            method='POST',
            endpoint=f'/api/preset',
            json=mock_preset)

        self.assertEqual(200, result.status_code)
        self.assertIsNotNone(result.json)

    async def test_update_preset(self):
        builder = TestData()

        mock_update_result = Mock()
        mock_update_result.modified_count = 1

        mock_preset = builder.get_preset()

        self.mock_preset_repository.preset_exists.return_value = get_mock_async_result(
            value=True)
        self.mock_preset_repository.update.return_value = get_mock_async_result(
            value=mock_update_result)

        result = await self.send_request(
            method='PUT',
            endpoint=f'/api/preset',
            json=mock_preset)

        self.assertEqual(200, result.status_code)
        self.assertIsNotNone(result.json)
