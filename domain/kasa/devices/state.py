from domain.kasa.device import KasaDevice
from domain.kasa.devices.light import KasaLight
from domain.kasa.preset import KasaPreset
from framework.serialization import Serializable
from framework.validators.nulls import not_none


class DeviceState:
    def __init__(self, data):
        self.device = data.get('kasa_device')
        self.preset = data.get('kasa_preset')

        not_none(self.device, 'device')
        not_none(self.preset, 'preset')

    @staticmethod
    def create_device_state(
        device: KasaDevice,
        preset: KasaPreset
    ) -> 'DeviceState':
        '''
        Factory method for device state
        from params
        '''

        return DeviceState({
            'kasa_device': device,
            'kasa_preset': preset
        })

    def to_json(self) -> dict:
        return {
            'kasa_device': self.device.to_json(),
            'kasa_preset': self.preset.to_json()
        }

    @property
    def kasa_device(self):
        return KasaDevice(
            data=self.device)

    @property
    def kasa_preset(self):
        return KasaPreset(
            data=self.preset)


class CachedDeviceState(Serializable):
    def __init__(self, device_id, device_type, preset_id, hash_key, power_state):
        self.device_id = device_id
        self.device_type = device_type
        self.preset_id = preset_id
        self.hash_key = hash_key
        self.power_state = power_state

        not_none(self.power_state, 'power_state')

    @staticmethod
    def get_default():
        return CachedDeviceState(
            device_id=None,
            device_type=None,
            preset_id=None,
            hash_key=None,
            power_state=False)


class StoredDeviceState:
    def __init__(self, device: KasaLight, preset: KasaPreset):
        self.preset = preset
        self.device = device

    def get_kasa_device(self):
        return self.preset.to_device_model(
            device=self.device)

    def to_request(self):
        return {
            'hash_key': self.get_kasa_device().get_hash(),
            'preset': self.preset.to_dict(),
            'device': self.device.to_dict()
        }
