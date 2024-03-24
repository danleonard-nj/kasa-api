import uuid
from datetime import datetime

from domain.exceptions import NullArgumentException
from framework.serialization import Serializable
from utils.helpers import DateTimeUtil


class KasaDevicePreset:
    def __init__(
        self,
        device_id: str,
        preset_id: str
    ):
        self.device_id = device_id
        self.preset_id = preset_id


class KasaSceneMapping:
    @property
    def device_ids(
        self
    ) -> list[str]:

        device_ids = set([
            x.device_id
            for x in self.mapping
        ])

        return list(device_ids)

    @property
    def preset_ids(
        self
    ) -> list[str]:
        preset_ids = set([
            x.preset_id
            for x in self.mapping
        ])

        return list(preset_ids)

    @property
    def mapping(
        self
    ) -> list[KasaDevicePreset]:
        return self.__mapping

    def __init__(self, mapping):
        self.__mapping = self._get_device_presets(
            mapping=mapping)

    def _get_device_presets(
        self,
        mapping
    ) -> list[KasaDevicePreset]:
        scene_mapping = list()

        # Shape of a scene mapping on the entity:
        # {
        #     "preset_id": "a7d25728-6e67-4a5e-8114-250a21b2662f",
        #     "devices": [
        #         "800695141FED00F88FB3140FA384F6991DA9B522"
        #     ]
        # }

        for preset_devices in mapping:
            preset_id = preset_devices.get('preset_id')
            device_ids = preset_devices.get('devices', [])

            device_presets = [KasaDevicePreset(
                device_id=device_id,
                preset_id=preset_id)
                for device_id in device_ids]

            scene_mapping.extend(device_presets)
        return scene_mapping


class KasaPresetDeviceMapping:
    def __init__(
        self,
        mapping: dict
    ):
        self.preset_id = mapping.get('preset_id')
        self.devices = mapping.get('devices')


class KasaScene(Serializable):
    def __init__(
        self,
        scene_id: str,
        scene_name: str,
        scene_category_id: str,
        mapping,
        flow,
        modified_date: int,
        created_date: int
    ):
        self.scene_id = scene_id
        self.scene_name = scene_name
        self.scene_category_id = scene_category_id
        self.mapping = mapping
        self.flow = flow
        self.modified_date = modified_date
        self.created_date = created_date

        # Other values are nullable when the
        # scene is first initialized

        NullArgumentException.if_none_or_whitespace(
            self.scene_name, 'scene_name')

    @staticmethod
    def from_dict(
        data: dict
    ):
        return KasaScene(
            scene_id=data.get('scene_id'),
            scene_name=data.get('scene_name'),
            scene_category_id=data.get('scene_category_id'),
            mapping=data.get('mapping'),
            flow=data.get('flow'),
            modified_date=data.get('modified_date'),
            created_date=data.get('created_date'))

    def get_selector(
        self
    ) -> dict:
        return {
            'scene_id': self.scene_id
        }

    def get_mapping(
        self
    ) -> list[KasaPresetDeviceMapping]:
        return [
            KasaPresetDeviceMapping(
                mapping=mapping)
            for mapping in self.mapping
        ]

    def get_scene_mapping(
        self
    ) -> KasaSceneMapping:
        return KasaSceneMapping(
            mapping=self.mapping)

    @staticmethod
    def create_scene(
        data: dict
    ) -> 'KasaScene':

        return KasaScene.from_dict(
            data=data | {
                'scene_id': str(uuid.uuid4()),
                'created_date': DateTimeUtil.timestamp()
            })


class KasaSceneCategory(Serializable):
    def __init__(
        self,
        scene_category_id: str,
        scene_category: str,
        created_date: int
    ):
        self.scene_category_id = scene_category_id
        self.scene_category = scene_category
        self.created_date = created_date

    def get_selector(
        self
    ) -> dict:
        return {
            'scene_category_id': self.scene_category_id
        }

    @staticmethod
    def from_entity(
        data: dict
    ):
        return KasaSceneCategory(
            scene_category_id=data.get('scene_category_id'),
            scene_category=data.get('scene_category'),
            created_date=data.get('created_date'))

    @staticmethod
    def create_category(
        category_name: str
    ) -> 'KasaSceneCategory':

        return KasaSceneCategory({
            'scene_category_id': str(uuid.uuid4()),
            'scene_category': category_name,
            'created_date': datetime.now()
        })
