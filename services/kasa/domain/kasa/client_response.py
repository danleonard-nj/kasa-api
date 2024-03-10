import uuid
from datetime import datetime
from typing import Dict

from domain.rest import UpdateClientResponseRequest
from framework.serialization import Serializable


class KasaClientResponse(Serializable):
    @property
    def is_error(
        self
    ) -> bool:
        return self._get_error_status()

    def __init__(
        self,
        client_response_id: str,
        device_id: str,
        preset_id: str,
        client_response: dict,
        state_key: str,
        created_date: str,
        modified_date: str
    ):
        self.client_response_id = client_response_id
        self.device_id = device_id
        self.preset_id = preset_id
        self.client_response = client_response
        self.state_key = state_key
        self.created_date = created_date
        self.modified_date = modified_date

    def from_entity(
        data: dict
    ):
        return KasaClientResponse(
            client_response_id=data.get('client_response_id'),
            device_id=data.get('device_id'),
            preset_id=data.get('preset_id'),
            client_response=data.get('client_response'),
            state_key=data.get('state_key'),
            created_date=data.get('created_date'),
            modified_date=data.get('modified_date'))

    def _get_error_status(
        self
    ) -> bool:
        if self.client_response is None:
            return False

        return self.client_response.get(
            'error_code', 0) < 0

    def get_selector(self):
        return {
            'client_response_id': self.client_response_id
        }

    def update_client_response(
        self,
        request: UpdateClientResponseRequest
    ):
        self.client_response = request.client_response
        self.preset_id = request.preset_id
        self.state_key = request.state_key

        self.modified_date = datetime.now()

    def update_sync_status(
        self,
        sync_status: str,
        sync_reason: str
    ):
        self.sync_status = sync_status
        self.sync_reason = sync_reason

        self.modified_date = datetime.now()

    @staticmethod
    def create_client_response(
        device_id: str,
        preset_id: str,
        client_response: Dict,
        state_key: str
    ):
        return KasaClientResponse(
            client_response_id=str(uuid.uuid4()),
            device_id=device_id,
            preset_id=preset_id,
            client_response=client_response,
            state_key=state_key,
            created_date=datetime.now(),
            modified_date=None)
