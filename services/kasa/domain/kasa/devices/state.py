from datetime import datetime
from typing import Dict
import uuid
from framework.serialization import Serializable


class KasaDeviceState(Serializable):
    def __init__(
        self,
        device_state_id: str,
        device_id: str,
        preset_id: str,
        state_key: str,
        modified_date: datetime,
        created_date: datetime
    ):
        self.device_state_id = device_state_id
        self.device_id = device_id
        self.preset_id = preset_id
        self.state_key = state_key
        self.modified_date = modified_date
        self.created_date = created_date

    def update_device_state(
        self,
        device_state: 'KasaDeviceState'
    ):
        self.preset_id = device_state.preset_id
        self.state_key = device_state.state_key
        self.modified_date = datetime.now()

    def get_selector(
        self
    ) -> Dict:
        return {
            'device_state_id': self.device_state_id
        }

    @ staticmethod
    def from_entity(
        data: Dict
    ):
        return KasaDeviceState(
            device_state_id=data.get('device_state_id'),
            device_id=data.get('device_id'),
            preset_id=data.get('preset_id'),
            state_key=data.get('state_key'),
            modified_date=data.get('modified_date'),
            created_date=data.get('created_date'))

    @ staticmethod
    def create_device_state(
        device_id: str,
        preset_id: str,
        state_key: str,
        power_state: bool
    ):
        return KasaDeviceState(
            device_state_id=str(uuid.uuid4()),
            device_id=device_id,
            preset_id=preset_id,
            state_key=state_key,
            created_date=datetime.now())
