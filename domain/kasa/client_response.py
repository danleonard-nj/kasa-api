from datetime import datetime
import uuid
from framework.serialization import Serializable

from domain.rest import UpdateClientResponseRequest


class KasaClientResponse(Serializable):
    def __init__(self, data):
        self.client_response_id = data.get('client_response_id')
        self.device_id = data.get('device_id')
        self.preset_id = data.get('preset_id')
        self.client_response = data.get('client_response')
        self.created_date = data.get('created_date')
        self.modified_date = data.get('modified_date')

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
        self.modified_date = datetime.now()

    @staticmethod
    def create_client_response(
        device_id: str,
        preset_id: str,
        client_response
    ):
        return KasaClientResponse({
            'client_response_id': str(uuid.uuid4()),
            'device_id': device_id,
            'preset_id': preset_id,
            'client_response': client_response,
            'created_date': datetime.now()
        })
