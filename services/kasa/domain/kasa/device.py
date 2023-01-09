from abc import abstractmethod
from typing import Dict

from framework.exceptions.nulls import ArgumentNullException
from framework.serialization import Serializable

from domain.common import Selectable
from domain.constants import KasaDeviceType
from domain.exceptions import InvalidDeviceTypeException
from domain.rest import KasaRequestBase


class KasaDevice(Serializable, Selectable):
    def __init__(self, data):
        self.device_id = data.get('device_id')
        self.device_name = data.get('device_name')
        self.device_type = data.get('device_type')
        self.device_sync = data.get('device_sync')
        self.region_id = data.get('region_id')

        ArgumentNullException.if_none_or_whitespace(
            self.device_id, 'device_id')
        ArgumentNullException.if_none_or_whitespace(
            self.device_name, 'device_name')

        self.__validate_device_type(
            device_type=self.device_type)

    def get_selector(
        self
    ) -> Dict:
        return {
            'device_id': self.device_id
        }

    @abstractmethod
    def state_key(
        self
    ) -> str:
        raise NotImplementedError()

    @abstractmethod
    def to_kasa_request(
        self,
        parameters: Dict
    ):
        '''
        Called from the derived device type class to
        build the request with generic `parameters`
        '''

        ArgumentNullException.if_none(parameters, 'parameters')

        # Build a device request wi/ specific device
        # type parameters passed in
        kasa_request = KasaRequestBase(
            device_id=self.device_id,
            request_data=parameters)

        return kasa_request.to_dict()

    @staticmethod
    def from_kasa_device_json_object(
        kasa_device: Dict
    ):
        '''
        Construct an `KasaDevice` instance 
        from raw JSON object data from the
        Kasa client API
        '''

        ArgumentNullException.if_none(kasa_device, 'data')

        device_id = kasa_device.get('deviceId')
        device_name = kasa_device.get('alias')
        device_type = kasa_device.get('deviceType')
        mic_type = kasa_device.get('mic_type')

        device_kwargs = dict(
            device_id=device_id,
            device_name=device_name,
            device_type=device_type or mic_type
        )

        return KasaDevice(device_kwargs)

    def __validate_device_type(
        self,
        device_type: str
    ):
        ArgumentNullException.if_none_or_whitespace(device_type, 'device_type')

        if device_type not in [KasaDeviceType.KasaLight,
                               KasaDeviceType.KasaPlug]:
            raise InvalidDeviceTypeException(
                device_type=device_type)

    def set_region(
        self,
        region_id: str
    ) -> None:
        '''
        Update the device's region
        '''

        ArgumentNullException.if_none_or_whitespace(region_id)
        self.region_id = region_id
