import uuid
from datetime import datetime

from domain.kasa.devices.state import CachedDeviceState


class DeviceHistory:
    def __init__(self, data):
        self.device_history_id = data.get(
            'device_history_id') or str(uuid.uuid4())
        self.device_id = data.get('device_id')
        self.device_type = data.get('device_type')
        self.preset_id = data.get('preset_id')
        self.hash_key = data.get('hash_key')
        self.power_state = data.get('power_state')
        self.created_date = data.get('created_date') or datetime.utcnow()

    def to_dict(self):
        return self.__dict__.copy()

    def to_cached_device_state(self):
        return CachedDeviceState(
            device_id=self.device_id,
            preset_id=self.preset_id,
            device_type=self.device_type,
            hash_key=self.hash_key,
            power_state=self.power_state)
