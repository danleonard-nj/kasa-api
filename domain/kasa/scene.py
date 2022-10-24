from datetime import datetime
import json
import uuid
from typing import List

from domain.rest import MappedSceneRequest
from framework.serialization import Serializable
from framework.validators.nulls import not_none


class KasaScene(Serializable):
    def __init__(self, data):
        self.scene_id = data.get('scene_id')
        self.scene_name = data.get('scene_name')
        self.scene_category_id = data.get('scene_category_id')
        self.mapping = data.get('mapping')
        self.flow = data.get('flow')

        # Other values are nullable when the
        # scene is first initialized
        not_none(self.scene_name, 'scene_name')

    def with_id(self, id=None) -> 'KasaScene':
        '''
        Set the scene ID to the provided value, or a
        new GUID if none is provided

        `id`: scene ID
        '''

        self.scene_id = id or str(uuid.uuid4())
        return self

    def get_device_preset_pairs(self) -> List[MappedSceneRequest]:
        '''
        Get mapping objects for presets to devices for
        event dispatch
        '''

        scene_maps = [
            KasaSceneMapping(x)
            for x in self.mapping]

        results = []
        for _map in scene_maps:
            pairs = _map.get_preset_device_pairs()
            results.extend([MappedSceneRequest(
                device_id=k,
                preset_id=v
            ) for k, v in pairs.items()])

        return results


class KasaSceneMapping:
    def __init__(self, data: dict):
        self.preset_id = data.get('preset_id')
        self.devices = data.get('devices')

        not_none(self.preset_id, 'preset_id')
        not_none(self.devices, 'devices')

    def get_preset_device_pairs(self):
        return {
            device: self.preset_id
            for device in self.devices
        }

    def to_json(self):
        return self.__dict__

    def to_string(self) -> str:
        return json.dumps(
            self,
            indent=True,
            default=str)


class KasaSceneCategory(Serializable):
    def __init__(
        self,
        data: dict
    ):
        self.scene_category_id = data.get('scene_category_id')
        self.scene_category = data.get('scene_category')
        self.created_date = data.get('created_date')

    @staticmethod
    def create_category(
        category_name: str
    ) -> 'KasaSceneCategory':
        return KasaSceneCategory({
            'scene_category_id': str(uuid.uuid4()),
            'scene_category': category_name,
            'created_date': datetime.now()
        })
