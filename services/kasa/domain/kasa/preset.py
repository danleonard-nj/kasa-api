import uuid
from typing import Dict, Union

from framework.exceptions.nulls import ArgumentNullException
from framework.serialization import Serializable

from domain.common import Selectable
from domain.constants import KasaDeviceType
from domain.kasa.device import KasaDevice
from domain.kasa.devices.light import KasaLight
from domain.kasa.devices.plug import KasaPlug
from domain.rest import KasaRequest
from utils.helpers import DateTimeUtil


class KasaDeviceHandler:
    @staticmethod
    def to_device_preset(
        device: KasaDevice,
        definition: Dict
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
        if device.device_type == KasaDeviceType.KasaPlug:
            return KasaPlug(**params)

        # Build Kasa light model
        if device.device_type == KasaDeviceType.KasaLight:
            return KasaLight(**params)


class KasaPreset(Serializable, Selectable):
    def __init__(
        self,
        preset_id: str,
        preset_name: str,
        device_type: str,
        definition: Dict,
        created_date: int,
        modified_date: int,
    ):
        self.preset_id = preset_id
        self.preset_name = preset_name
        self.device_type = device_type
        self.definition = definition
        self.created_date = created_date
        self.modified_date = modified_date

        ArgumentNullException.if_none_or_whitespace(
            self.preset_name, 'preset_name')
        ArgumentNullException.if_none_or_whitespace(
            self.device_type, 'device_type')
        ArgumentNullException.if_none(
            self.definition, 'definition')

    @staticmethod
    def from_dict(
        data: Dict
    ):
        return KasaPreset(
            preset_id=data.get('preset_id'),
            preset_name=data.get('preset_name'),
            device_type=data.get('device_type'),
            definition=data.get('definition'),
            created_date=data.get('created_date'),
            modified_date=data.get('modified_date')
        )

    def get_selector(
        self
    ) -> Dict:

        return {
            'preset_id': self.preset_id
        }

    def update_preset(
        self,
        preset_name: str,
        device_type: str,
        definition: Dict
    ):
        ArgumentNullException.if_none_or_whitespace(
            preset_name, 'preset_name')
        ArgumentNullException.if_none_or_whitespace(
            device_type, 'device_type')
        ArgumentNullException.if_none(
            definition, 'definition')

        self.preset_name = preset_name
        self.device_type = device_type
        self.definition = definition
        self.modified_date = DateTimeUtil.timestamp()

    @staticmethod
    def create_preset(
        data: Dict
    ):
        return KasaPreset.from_dict(
            data=data | {
                'preset_id': str(uuid.uuid4()),
                'created_date': DateTimeUtil.timestamp(),
            }
        )

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
