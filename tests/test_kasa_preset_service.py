from sys import get_asyncgen_hooks

import pytest
from data.repositories.kasa_device_repository import KasaDeviceRepository
from data.repositories.kasa_preset_repository import KasaPresetRepository
from domain.constants import KasaDeviceType
from services.kasa_preset_service import KasaPresetSevice
from domain.rest import GetPresetRequest
from utils.helpers import TestData, get_mock_async_result
from unittest.mock import Mock
import unittest

from framework.testing.mocks import MockContainer
from framework.testing.helpers import guid


@pytest.mark.asyncio
class KasaPresetServiceTests(unittest.IsolatedAsyncioTestCase):
    def _side_effect_resolve(self, _type):
        if _type == KasaPresetRepository:
            return self.preset_repository
        if _type == KasaDeviceRepository:
            return self.device_repository

    def setUp(self) -> None:
        container = MockContainer()

        self.preset_repository = Mock()
        self.device_repository = Mock()

        container.define(
            KasaPresetRepository,
            self.preset_repository)
        container.define(
            KasaDeviceRepository,
            self.device_repository)

        self.service = KasaPresetSevice(
            container=container)
        self.test_data = TestData()

    async def test_create_preset(self):
        self.preset_repository.preset_exists = Mock(
            return_value=get_mock_async_result(
                value=False))

        insert_result = Mock()
        insert_result.inserted_id = 'test-id'

        self.preset_repository.insert = Mock(
            return_value=get_mock_async_result(
                value=insert_result))

        preset_name = 'test-preset'
        device_type = KasaDeviceType.KasaLight

        result = await self.service.create_preset({
            'preset_name': preset_name,
            'device_type': device_type,
            'definition': {}
        })

        assert(result != None)
        assert(result.get('preset_name') == preset_name)
        assert(result.get('device_type') == device_type)

    async def test_update_preset(self):
        preset_id = guid()
        preset_name = guid()
        device_type = KasaDeviceType.KasaLight
        definition = guid()

        self.preset_repository.preset_exists = Mock(
            return_value=get_mock_async_result(
                value=True))

        update_result = Mock()
        update_result.modified_count = 1

        self.preset_repository.update = Mock(
            return_value=get_mock_async_result(
                value=update_result))

        result = await self.service.update_preset({
            'preset_id': preset_id,
            'preset_name': preset_name,
            'device_type': device_type,
            'definition': definition
        })

        self.assertEqual(result.get('preset_id'), preset_id)
        self.assertEqual(result.get('preset_name'), preset_name)
        self.assertEqual(result.get('device_type'), device_type)
        self.assertEqual(result.get('definition'), definition)

    async def test_get_preset(self):
        preset_id = guid()
        preset_name = guid()
        device_type = KasaDeviceType.KasaLight
        definition = guid()

        data = {
            'preset_id': preset_id,
            'preset_name': preset_name,
            'device_type': device_type,
            'definition': definition
        }

        self.preset_repository.get = Mock(
            return_value=get_mock_async_result(
                value=data))

        preset = await self.service.get_preset(
            preset_id=preset_id)

        self.assertEqual(preset.get('preset_id'), preset_id)
        self.assertEqual(preset.get('preset_name'), preset_name)
        self.assertEqual(preset.get('device_type'), device_type)
        self.assertEqual(preset.get('definition'), definition)

    async def test_get_all_presets(self):
        presets = [self.test_data.get_preset() for x in range(50)]
        preset_ids = [x.get('preset_id') for x in presets]

        self.preset_repository.get_all = Mock(
            return_value=get_mock_async_result(
                value=presets))

        result = await self.service.get_all_presets()

        self.assertEqual(len(presets), len(result.get('presets')))
        self.assertTrue('presets' in result)
        self.assertTrue(
            all([x.get('preset_id') in preset_ids for x in result.get('presets')]))

    async def test_get_preset_request(self):
        device = self.test_data.get_light_device()
        preset = self.test_data.get_preset()

        definition = preset.get('definition')

        device_id = device.get('device_id')
        preset_id = preset.get('preset_id')

        self.device_repository.get = Mock(
            return_value=get_mock_async_result(
                value=device))

        self.preset_repository.get = Mock(
            return_value=get_mock_async_result(
                value=preset))

        preset_request = GetPresetRequest({
            'preset_id': preset_id,
            'device_id': device_id
        })

        request = await self.service.get_preset_request(
            request=preset_request)

        self.assertIsNotNone(request)

        kasa_method = request.get(
            'method')
        kasa_params = request.get(
            'params')
        kasa_request_data = kasa_params.get(
            'requestData')
        kasa_light = kasa_request_data.get(
            'smartlife.iot.smartbulb.lightingservice')
        kasa_light_state = kasa_light.get(
            'transition_light_state')

        self.assertIsNotNone(kasa_method)

        self.assertEqual(
            first=kasa_method,
            second='passthrough')

        self.assertIsNotNone(kasa_params)
        self.assertIsNotNone(kasa_request_data)
        self.assertIsNotNone(kasa_light)
        self.assertIsNotNone(kasa_light_state)

        self.assertEqual(
            first=kasa_light_state.get('mode'),
            second='normal')
        self.assertEqual(
            first=kasa_light_state.get('saturation'),
            second=definition.get('saturation'))
        self.assertEqual(
            first=kasa_light_state.get('brightness'),
            second=definition.get('brightness'))
        self.assertEqual(
            first=kasa_light_state.get('hue'),
            second=definition.get('hue'))
        self.assertIsNone(
            first=kasa_light_state.get('temperature'),
            second=definition.get('color_temp'))
        self.assertEqual(
            first=kasa_light_state.get('on_off'),
            second=1)

    async def test_delete_preset(self):
        preset = self.test_data.get_preset()
        preset_id = preset.get('preset_id')

        self.preset_repository.get = Mock(
            return_value=get_mock_async_result(
                value=preset))

        self.preset_repository.delete = Mock(
            return_value=get_mock_async_result(
                value=None))

        result = await self.service.delete_preset(
            preset_id=preset_id)

        self.assertIsNotNone(result)
        self.assertEqual(
            first=result.get('deleted'),
            second=preset_id)
