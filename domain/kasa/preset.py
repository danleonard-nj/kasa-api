import uuid
from typing import Union

from framework.serialization import Serializable
from framework.validators.nulls import not_none

from domain.cache import Cacheable
from domain.common import Selectable
from domain.constants import KasaDeviceType
from domain.exceptions import NullArgumentException
from domain.kasa.device import KasaDevice
from domain.kasa.devices.light import KasaLight
from domain.kasa.devices.plug import KasaPlug
from domain.rest import KasaRequest
from framework.exceptions.nulls import ArgumentNullException


class KasaPreset(Serializable, Cacheable, Selectable):
    def __init__(self, data):
        self.preset_id = data.get('preset_id')
        self.preset_name = data.get('preset_name')
        self.device_type = data.get('device_type')
        self.definition = data.get('definition')

        ArgumentNullException.if_none_or_whitespace(
            self.preset_name, 'preset_name')
        ArgumentNullException.if_none_or_whitespace(
            self.device_type, 'device_type')
        ArgumentNullException.if_none(
            self.definition, 'definition')

    def get_selector(self):
        return {
            'preset_id': self.preset_id
        }

    @staticmethod
    def create_preset(data):
        return KasaPreset(
            data=data | {
                'preset_id': (uuid.uuid4())
            }
        )

    # @property
    # def power_state(self) -> int:
    #     return self.definition.get('state')

    # @power_state.setter
    # def power_state(
    #     self,
    #     state
    # ):
    #     self.definition['state'] = state

    def to_device_preset(
        self,
        device: KasaDevice
    ) -> Union[KasaPlug, KasaLight]:
        '''
        Parse the device type (light, plug, etc) with
        preset parameters
        '''

        ArgumentNullException.if_none(device, 'device')

        # Base params (consistent across all device
        # types)
        default_params = {
            'device_id': device.device_id,
            'device_type': device.device_type,
            'device_name': device.device_name,
        }

        params = default_params | self.definition

        # Build Kasa plug model
        if self.device_type == KasaDeviceType.KasaPlug:
            return KasaPlug(**params)

        # Build Kasa light model
        if self.device_type == KasaDeviceType.KasaLight:
            return KasaLight(**params)

    def to_request(
        self,
        device: KasaDevice
    ) -> KasaRequest:
        ArgumentNullException.if_none(device, 'device')

        request_body = self.to_device_preset(
            device).to_kasa_request()

        return KasaRequest({
            'device_id': device.device_id,
            'preset_id': self.preset_id,
            'request_body': request_body
        })
