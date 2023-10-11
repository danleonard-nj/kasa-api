from typing import Dict, Union

from framework.crypto.hashing import sha256
from framework.exceptions.nulls import ArgumentNullException

from domain.common import Hashable
from domain.constants import KasaDeviceType
from domain.kasa.device import KasaDevice
from domain.rest import KasaResponse
from utils.helpers import generate_key


class KasaLight(KasaDevice, Hashable):
    def __init__(
        self,
        device_id: str,
        device_name: str,
        state: bool,
        brightness: Union[int, float],
        hue: Union[int, float],
        saturation: Union[int, float],
        temperature: Union[int, float] = 0,
        **kwargs
    ):

        self.state = state
        self.device_id = device_id
        self.device_name = device_name
        self.brightness = brightness
        self.hue = hue
        self.saturation = saturation
        self.temperature = temperature

        super().__init__({
            'device_id': device_id,
            'device_name': device_name,
            'device_type': KasaDeviceType.KasaLight
        })

        ArgumentNullException.if_none_or_whitespace(
            self.device_id, 'device_id')
        ArgumentNullException.if_none_or_whitespace(
            self.device_name, 'device_name')
        ArgumentNullException.if_none_or_whitespace(
            self.device_type, 'device_type')

        ArgumentNullException.if_none_or_whitespace(self.state, 'state')

        ArgumentNullException.if_none(self.brightness, 'brightness')
        ArgumentNullException.if_none(self.hue, 'hue')
        ArgumentNullException.if_none(self.saturation, 'saturation')

    def state_key(
        self
    ) -> str:
        params = [self.state,
                  self.saturation,
                  self.brightness,
                  self.hue,
                  self.temperature]

        return generate_key(
            items=params)

    @staticmethod
    def from_kasa_response(
        kasa_response: KasaResponse
    ) -> Union['KasaLight', None]:
        '''
        Construct a `KasaLight` instance from the device
        info response from the Kasa client
        '''

        ArgumentNullException.if_none(kasa_response, 'kasa_response')

        # TODO: Throw here, handle scenario upstream
        if not kasa_response.has_result:
            return

        # Base device object
        device = KasaDevice.from_device_json_object(
            kasa_device=kasa_response.device_object)

        # Light on/off
        light_power_state = kasa_response.device_object.get(
            'light_state').get('on_off')

        # Get the light device parameters
        light_params = kasa_response.device_object.get(
            'light_state')

        # Get the nested default light params if they're present
        if 'dft_on_state' in light_params:
            light_params = light_params.get('dft_on_state')

        return KasaLight(
            device_id=device.device_id,
            device_name=device.device_name,
            state=light_power_state == 1,
            brightness=light_params.get('brightness'),
            hue=light_params.get('hue'),
            saturation=light_params.get('saturation'),
            temperature=light_params.get('color_temp'))

    def to_kasa_request(
        self
    ) -> Dict:
        transition_light_state = dict(
            mode='normal',
            saturation=self.saturation,
            brightness=self.brightness,
            hue=self.hue,
            on_off=1 if self.state else 0,
            color_temp=self.temperature,
            ignore_default=1
        )

        return super().to_kasa_request({
            'smartlife.iot.smartbulb.lightingservice': {
                'transition_light_state': transition_light_state
            }
        })
