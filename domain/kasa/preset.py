import uuid
from typing import Union

from domain.constants import KasaDeviceType
from domain.kasa.device import KasaDevice
from domain.kasa.devices.light import KasaLight
from domain.kasa.devices.plug import KasaPlug
from domain.rest import KasaRequest
from framework.serialization import Serializable
from framework.validators.nulls import not_none


class KasaPreset(Serializable):
    def __init__(self, data):
        self.preset_id = data.get('preset_id')
        self.preset_name = data.get('preset_name')
        self.device_type = data.get('device_type')
        self.definition = data.get('definition')

        not_none(self.preset_name, 'preset_name')
        not_none(self.definition, 'definition')

    def to_json(self):
        return self.__dict__

    def clone(self):
        return KasaPreset(data={
            'preset_id': self.preset_id,
            'preset_name': self.preset_name,
            'device_type': self.device_type,
            'definition': self.definition.copy()
        })

    def with_id(self, id=None):
        self.preset_id = id or str(uuid.uuid4())
        return self

    @property
    def power_state(self) -> int:
        return self.definition.get('state')

    @power_state.setter
    def power_state(
        self,
        state
    ):
        self.definition['state'] = state

    def to_device_model(self, device: KasaDevice) -> Union[KasaPlug, KasaLight]:
        not_none(device, 'device')

        _params = {
            'device_id': device.device_id,
            'device_type': device.device_type,
            'device_name': device.device_name,
        }
        params = _params | self.definition

        if self.device_type == KasaDeviceType.KasaPlug:
            return KasaPlug(**params)

        if self.device_type == KasaDeviceType.KasaLight:
            return KasaLight(**params)

    def to_request(
        self,
        device: KasaDevice
    ) -> KasaRequest:
        not_none(device, 'device')

        request_body = self.to_device_model(
            device).to_kasa_request()

        return KasaRequest({
            'device_id': device.device_id,
            'preset_id': self.preset_id,
            'request_body': request_body
        })
