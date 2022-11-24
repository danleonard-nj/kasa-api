from abc import abstractmethod

from framework.serialization import Serializable
from framework.validators.nulls import not_none

from domain.common import Selectable
from domain.constants import KasaDeviceType
from domain.exceptions import NullArgumentException
from domain.rest import KasaRequestBase


class KasaDevice(Serializable, Selectable):
    def __init__(self, data):
        self.device_id = data.get('device_id')
        self.device_name = data.get('device_name')
        self.device_type = data.get('device_type')
        self.region_id = data.get('region_id')

        not_none(self.device_id, 'device_id')
        not_none(self.device_name, 'device_name')

        self._validate_device_type(
            device_type=self.device_type)

    def get_selector(
        self
    ) -> dict:
        return {
            'device_id': self.device_id
        }

    def to_kasa_request(self, parameters):
        not_none(parameters, 'parameters')

        return KasaRequestBase(
            device_id=self.device_id,
            request_data=parameters).to_dict()

    @staticmethod
    def from_kasa_device_params(data):
        not_none(data, 'data')

        return KasaDevice({
            'device_id': data.get('deviceId'),
            'device_name': data.get('alias'),
            'device_type': (data.get('deviceType')
                            or data.get('mic_type'))
        })

    def to_display_model(self):
        return {
            k: v for k, v in self.__dict__.items()
        }

    def _validate_device_type(self, device_type):
        not_none(device_type, 'device_type')

        if device_type not in [KasaDeviceType.KasaLight, KasaDeviceType.KasaPlug]:
            raise Exception(f'Unsupported device type: {device_type}')

    def set_region(
        self,
        region_id: str
    ) -> None:
        '''
        Update the device's region
        '''

        NullArgumentException.if_none_or_whitespace(region_id)

        self.region_id = region_id
