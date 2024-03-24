from abc import abstractmethod
from typing import Literal

from domain.constants import KasaDeviceType
from domain.exceptions import InvalidDeviceTypeException
from domain.rest import KasaApiRequest
from framework.exceptions.nulls import ArgumentNullException
from framework.serialization import Serializable


class KasaDevice(Serializable):
    def __init__(
        self,
        data: dict
    ):
        self.device_id = data.get('device_id')
        self.device_name = data.get('device_name')
        self.device_type = data.get('device_type')
        self.device_sync = data.get('device_sync')
        self.region_id = data.get('region_id')

        ArgumentNullException.if_none_or_whitespace(
            self.device_id, 'device_id')
        ArgumentNullException.if_none_or_whitespace(
            self.device_name, 'device_name')

        self._validate_device_type(
            device_type=self.device_type)

    def get_selector(
        self
    ) -> dict:
        return {
            'device_id': self.device_id
        }

    @abstractmethod
    def state_key(
        self
    ) -> str:
        raise NotImplementedError()

    def update_device(
        self,
        device_name: str,
        device_type: str,
        region_id: str
    ):
        ArgumentNullException.if_none_or_whitespace(device_name, 'device_name')
        ArgumentNullException.if_none_or_whitespace(device_type, 'device_type')

        self.device_name = device_name
        self.device_type = device_type
        self.region_id = region_id
        return self

    @abstractmethod
    def to_kasa_request(
        self,
        parameters: dict
    ):
        '''
        Called from the derived device type class to
        build the request with generic `parameters`
        '''

        ArgumentNullException.if_none(parameters, 'parameters')

        # Build a device request wi/ specific device
        # type parameters passed in
        kasa_request = KasaApiRequest(
            device_id=self.device_id,
            request_data=parameters)

        return kasa_request.to_dict()

    @staticmethod
    def from_device_json_object(
        kasa_device: dict
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

    def _validate_device_type(
        self,
        device_type: str
    ):
        ArgumentNullException.if_none_or_whitespace(device_type, 'device_type')

        if device_type not in [KasaDeviceType.KasaLight,
                               KasaDeviceType.KasaPlug,
                               KasaDeviceType.KasaCamera]:
            raise InvalidDeviceTypeException(
                device_type=device_type)

    def set_region(
        self,
        region_id: str
    ) -> None:
        '''
        Update the device's region
        '''

        ArgumentNullException.if_none_or_whitespace(region_id, 'region_id')

        self.region_id = region_id


class DeviceLog(Serializable):
    def __init__(
        self,
        log_id: str,
        timestamp: int,
        level: Literal['INFO', 'ERROR'],
        device_id: str,
        device_name: str,
        preset_id: str,
        preset_name: str,
        state_key: str,
        message: str
    ):
        self.log_id = log_id
        self.timestamp = timestamp
        self.level = level
        self.device_id = device_id
        self.device_name = device_name
        self.preset_id = preset_id
        self.preset_name = preset_name
        self.state_key = state_key
        self.message = message

    @staticmethod
    def from_entity(
        data: dict
    ):
        return DeviceLog(
            log_id=data.get('log_id'),
            timestamp=data.get('timestamp'),
            level=data.get('level'),
            device_id=data.get('device_id'),
            device_name=data.get('device_name'),
            preset_id=data.get('preset_id'),
            preset_name=data.get('preset_name'),
            state_key=data.get('state_key'),
            message=data.get('message'))
