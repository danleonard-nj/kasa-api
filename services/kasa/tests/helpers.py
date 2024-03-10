import uuid
from datetime import datetime

from domain.kasa.client_response import KasaClientResponse


class TestHelper:
    SCENE_ID = '71a60249-cd4b-4696-ae4c-24a9e0642dd6'

    def guid(self):
        return str(uuid.uuid4())

    def get_scene(self, **kwargs):
        default_scene = {
            'scene_id': self.guid(),
            'scene_name': self.guid(),
            'scene_category_id': self.guid(),
            'mapping': list(),
            'flow': dict()
        }

        return default_scene | kwargs

    def get_test_device(self, **kwargs):
        device = {
            "device_id": self.guid(),
            "device_name": self.guid(),
            "device_type": "IOT.SMARTPLUGSWITCH",
            "region_id": self.guid()
        }

        return device | kwargs

    def get_test_preset(self, **kwargs):
        preset = {
            "preset_id": self.guid(),
            "preset_name": self.guid(),
            "device_type": "IOT.SMARTPLUGSWITCH",
            "definition": {
                "state": True
            }
        }

        return preset | kwargs

    def get_create_preset_request(self, **kwargs):
        preset = {
            "definition": {
                "brightness": 0,
                "hue": 0,
                "saturation": 0,
                "state": False,
                "temperature": 0
            },
            "device_type": "IOT.SMARTBULB",
            "preset_id": self.guid(),
            "preset_name": self.guid()
        }

        return preset | kwargs

    def get_test_scene(self, **kwargs):
        scene = {
            "scene_id": self.guid(),
            "scene_name": self.guid(),
            "scene_category_id": self.guid(),
            "mapping": [
                {
                    "preset_id": self.guid(),
                    "devices": [self.guid() for _ in range(10)]
                },
                {
                    "preset_id": self.guid(),
                    "devices": [self.guid() for _ in range(10)]
                }
            ]
        }

        return scene | kwargs

    def get_mock_client_response(self, device_id):
        return KasaClientResponse(
            client_response_id=self.guid(),
            device_id=device_id,
            preset_id=self.guid(),
            client_response=dict(),
            created_date=datetime.now(),
            modified_date=datetime.now()
        )

    def get_mock_device(self, region_id=None):
        return {
            'device_id': self.guid(),
            'device_name': self.guid(),
            'device_type': 'IOT.SMARTPLUGSWITCH',
            'region_id': region_id
        }
