from datetime import datetime
from typing import Dict

from azure.servicebus import ServiceBusMessage
from framework.serialization import Serializable
from framework.serialization.utilities import serialize


class ApiMessage(Serializable):
    def __init__(
        self,
        base_url: str,
        method: str,
        token: str
    ):
        self.endpoint = self.get_endpoint(
            base_url=base_url)

        self.method = method
        self.json = self.get_body()
        self.headers = self.get_headers(
            token=token)

    def get_delay(
        _timedelta
    ):
        return None

    def get_body(
        self
    ) -> dict:
        pass

    def get_endpoint(
        self,
        base_url
    ) -> str:
        pass

    def get_headers(
        self,
        token: str
    ) -> str:

        return {
            'Authorization': f'Bearer {token}'
        }

    def to_service_bus_message(
        self
    ) -> ServiceBusMessage:

        message = ServiceBusMessage(
            body=serialize({
                'endpoint': self.endpoint,
                'method': self.method,
                'headers': self.headers,
                'content': self.json
            }))

        if self.get_delay() is not None:
            scheduled = datetime.utcnow() + self.get_delay()
            message.scheduled_enqueue_time_utc = scheduled

        return message


class StoreKasaClientResponseEvent(ApiMessage):
    def __init__(
        self,
        kasa_response: dict,
        device_id: str,
        preset_id: str,
        state_key: str,
        base_url: str,
        token: str
    ):
        self.kasa_response = kasa_response
        self.device_id = device_id
        self.preset_id = preset_id
        self.state_key = state_key

        super().__init__(
            base_url,
            'POST',
            token)

    def get_body(
        self
    ) -> dict:
        return {
            'device_id': self.device_id,
            'preset_id': self.preset_id,
            'client_response': self.kasa_response,
            'state_key': self.state_key
        }

    def get_endpoint(
        self,
        base_url: str
    ) -> str:
        return f'{base_url}/api/event/device/response'


class SetDeviceStateEvent(ApiMessage):
    def __init__(
        self,
        body: Dict,
        base_url: str,
        token: str
    ):
        self.__body = body

        super().__init__(
            base_url,
            'POST',
            token)

    def get_body(
        self
    ) -> dict:
        return self.__body

    def get_endpoint(
        self,
        base_url: str
    ) -> str:
        return f'{base_url}/api/event/device/state'
