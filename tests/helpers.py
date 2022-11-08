

import uuid


class TestHelper:
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
