from domain.common import Hashable
from domain.constants import KasaDeviceType, KasaRest
from domain.kasa.device import KasaDevice
from domain.rest import KasaResponse
from framework.validators.nulls import not_none


class KasaPlug(KasaDevice, Hashable):
    def __init__(
            self,
            device_id: str,
            device_name: str,
            state: bool,
            **kwargs):

        self.state = state

        super().__init__({
            'device_id': device_id,
            'device_name': device_name,
            'device_type': KasaDeviceType.KasaPlug
        })

    def get_power_state(self):
        not_none(self.state, 'state')

        return self.state

    def to_json(self):
        device = {
            'state': self.state
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

            return KasaPlug(
                device_id=device.device_id,
                device_name=device.device_name,
                state=info.get(KasaRest.RELAY_STATE) == 1)

    def to_kasa_request(self):
        return super().to_kasa_request({
            KasaRest.SYSTEM: {
                KasaRest.SET_RELAY_STATE: {
                    KasaRest.STATE: 1 if self.state else 0
                }
            }
        })

    @property
    def power_state(self):
        return self.state
