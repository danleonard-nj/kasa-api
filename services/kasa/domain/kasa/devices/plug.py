from typing import Dict, Union

from framework.exceptions.nulls import ArgumentNullException

from domain.common import Hashable
from domain.constants import KasaDeviceType
from domain.kasa.device import KasaDevice
from domain.rest import KasaResponse
from utils.helpers import generate_key


class KasaPlug(KasaDevice, Hashable):
    def __init__(
        self,
        device_id: str,
        device_name: str,
        state: bool,
        **kwargs
    ):

        self.state = state

        super().__init__({
            'device_id': device_id,
            'device_name': device_name,
            'device_type': KasaDeviceType.KasaPlug
        })

    def state_key(
        self
    ) -> str:
        params = [self.state]

        return generate_key(
            items=params)

    @staticmethod
    def from_kasa_response(
        kasa_response: KasaResponse
    ) -> Union['KasaPlug', None]:

        ArgumentNullException.if_none(kasa_response, 'kasa_response')

        if not kasa_response.has_result:
            return

        # Create the base Kasa device
        device = KasaDevice.from_device_json_object(
            kasa_device=kasa_response.device_object)

        # Get the power state (on/off)
        power_state = kasa_response.device_object.get('relay_state')

        return KasaPlug(
            device_id=device.device_id,
            device_name=device.device_name,
            state=power_state == 1)

    def to_kasa_request(
        self
    ) -> Dict:
        '''
        Generate the Kasa request to set the
        device state
        '''

        return super().to_kasa_request({
            'system': {
                'set_relay_state': {
                    'state': 1 if self.state else 0
                }
            }
        })
