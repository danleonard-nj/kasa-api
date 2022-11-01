import pytest
from domain.constants import KasaDeviceType
from domain.kasa import (
    KasaDevice,
    KasaPreset,
    KasaRequestBase,
    MappedSceneRequest
)
from domain.rest import (
    CreateSceneRequest,
    GetPresetRequest,
    UpdateSceneRequest
)
from utils.helpers import TestData
import unittest

from framework.testing.helpers import guid


@pytest.mark.asyncio
class KasaMappingTests(unittest.IsolatedAsyncioTestCase):
    def test_mapped_scene_request(self):
        device_id = guid()
        preset_id = guid()

        mapped_scene_request = MappedSceneRequest(
            device_id=device_id,
            preset_id=preset_id)

        assert(mapped_scene_request.preset_id == preset_id)
        assert(mapped_scene_request.device_id == device_id)

    def test_kasa_request_base(self):
        method = 'passthrough'
        device_id = guid()
        request_data = {'data': guid()}

        request_base = KasaRequestBase(
            device_id=device_id,
            request_data=request_data,
            method=method)

        request_base_default_method = KasaRequestBase(
            device_id=device_id,
            request_data=request_data)

        request_base_json = request_base.to_dict()

        assert(request_base_default_method.method == 'passthrough')
        assert(request_base.device_id == device_id)
        assert(request_base.request_data == request_data)

        assert(request_base_json.get('method') == 'passthrough')
        assert request_base_json == {
            'method': 'passthrough',
            'params': {'deviceId': device_id, 'requestData': request_data}
        }

    def test_kasa_device(self):
        device_id = guid()
        device_name = guid()
        device_type = KasaDeviceType.KasaLight
        preset_id = guid()

        kasa_device = KasaDevice({
            'device_id': device_id,
            'device_name': device_name,
            'device_type': device_type,
            'preset_id': preset_id
        })

        def create_invalid_device():
            invalid_device_type = KasaDevice({
                'device_id': device_id,
                'device_name': device_name,
                'device_type': 'invalid',
                'preset_id': preset_id
            })

        display_model = kasa_device.to_display_model()

        self.assertEqual(kasa_device.preset_id, preset_id)
        self.assertEqual(kasa_device.device_name, device_name)
        self.assertEqual(kasa_device.device_id, device_id)
        self.assertEqual(kasa_device.device_type, device_type)

        self.assertNotIn('preset_id', display_model)
        self.assertRaises(Exception, create_invalid_device)

    def test_get_preset_request(self):
        device_id = guid()
        preset_id = guid()

        def create_invalid_request():
            request = GetPresetRequest(
                data={
                    'preset_id': None,
                    'device_id': None
                }
            )

        request = GetPresetRequest({
            'preset_id': preset_id,
            'device_id': device_id
        })

        self.assertEqual(request.device_id, device_id)
        self.assertEqual(request.preset_id, preset_id)
        self.assertRaises(Exception, create_invalid_request)

    def test_update_scene_request(self):
        scene_id = guid()
        scene_name = guid()
        mapping = guid()
        flow = guid()

        request = UpdateSceneRequest(
            data={
                'scene_id': scene_id,
                'scene_name': scene_name,
                'mapping': mapping,
                'flow': flow
            }
        )

        def create_invalid_request():
            request = UpdateSceneRequest(
                data={
                    'scene_id': None,
                    'scene_name': None,
                    'mapping': None,
                    'flow': None
                }
            )

        self.assertEqual(scene_id, request.scene_id)
        self.assertEqual(scene_name, request.scene_name)
        self.assertEqual(mapping, request.mapping)
        self.assertEqual(flow, request.flow)
        self.assertRaises(Exception, create_invalid_request)

    def test_create_scene_request(self):
        scene_name = guid()
        mapping = guid()
        flow = guid()

        request = CreateSceneRequest(
            data={'scene_name': scene_name,
                  'mapping': mapping,
                  'flow': flow}
        )

        def create_invalid_request():
            CreateSceneRequest({
                'scene_name': None,
                'mapping': None,
                'flow': None
            })

        self.assertEqual(request.scene_name, scene_name)
        self.assertEqual(request.mapping, mapping)
        self.assertEqual(request.flow, flow)
        self.assertRaises(Exception, create_invalid_request)

    def test_kasa_preset(self):
        test_data = TestData()

        preset_id = guid()
        preset_name = guid()
        device_type = KasaDeviceType.KasaLight
        definition = test_data.get_preset_definition()

        preset = KasaPreset({
            'preset_id': preset_id,
            'preset_name': preset_name,
            'device_type': device_type,
            'definition': definition
        })

        preset.definition['state'] = False
        self.assertFalse(preset.power_state)

        preset.definition['state'] = True
        self.assertTrue(preset.power_state)

        kasa_device = KasaDevice(test_data.get_light_device())
        device_model = preset.to_device_model(kasa_device)

        self.assertEqual(device_model.device_id, kasa_device.device_id)
        self.assertEqual(device_model.device_type,
                         kasa_device.device_type)
        self.assertEqual(device_model.device_name,
                         kasa_device.device_name)

        new_id = guid()
        self.assertEqual(preset_id, preset.preset_id)
        preset.with_id(new_id)
        self.assertEqual(new_id, preset.preset_id)

        kasa_request_device = KasaDevice(test_data.get_light_device() | {
            'preset_id': preset.preset_id
        })

        kasa_request = preset.to_request(kasa_request_device)

        self.assertEqual(kasa_request_device.device_id, kasa_request.device_id)
        self.assertEqual(kasa_request_device.preset_id, kasa_request.preset_id)
