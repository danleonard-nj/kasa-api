from typing import Union

from domain.common import Hashable
from domain.constants import KasaDeviceType, KasaRest
from domain.kasa.device import KasaDevice
from domain.rest import KasaResponse
from framework.validators.nulls import not_none


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

        not_none(self.state, 'state')
        not_none(self.brightness, 'brightness')
        not_none(self.hue, 'hue')
        not_none(self.saturation, 'saturation')

        super().__init__({
            'device_id': device_id,
            'device_name': device_name,
            'device_type': KasaDeviceType.KasaLight
        })

    def to_dict(self):
        device = {
            'state': self.state,
            'hue': self.hue,
            'saturation': self.saturation,
            'temperature': self.temperature
        }

        return super().to_dict() | device

    @staticmethod
    def from_kasa_response(data: KasaResponse):
        not_none(data, 'data')

        if data.has_result:
            info = data.result.get(
                KasaRest.RESPONSE_DATA).get(
                    KasaRest.SYSTEM).get(
                        KasaRest.GET_SYSINFO)

            device = KasaDevice.from_kasa_device_params(
                data=info)

            light_state = info.get(KasaRest.LIGHT_STATE)

            if KasaRest.DEFAULT_LIGHT_STATE in light_state:
                light_state = light_state.get(KasaRest.DEFAULT_LIGHT_STATE)

            return KasaLight(
                device_id=device.device_id,
                device_name=device.device_name,
                state=light_state.get(KasaRest.ON_OFF) == 1,
                brightness=light_state.get(KasaRest.BRIGHTNESS),
                hue=light_state.get(KasaRest.HUE),
                saturation=light_state.get(KasaRest.SATURATION),
                temperature=light_state.get(KasaRest.COLOR_TEMP))

    def to_kasa_request(self):
        return super().to_kasa_request({
            KasaRest.LIGHTING_SERVICE: {
                KasaRest.TRANSITION_LIGHT_STATE: {
                    KasaRest.MODE: KasaRest.NORMAL,
                    KasaRest.SATURATION: self.saturation,
                    KasaRest.BRIGHTNESS: self.brightness,
                    KasaRest.HUE: self.hue,
                    KasaRest.ON_OFF: 1 if self.state else 0,
                    KasaRest.COLOR_TEMP: self.temperature,
                    KasaRest.IGNORE_DEFAULT: 1
                }
            }
        })
