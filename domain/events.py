from datetime import datetime, timedelta

from azure.servicebus import ServiceBusMessage
from framework.serialization.utilities import serialize

from domain.common import Serializable
from domain.kasa.devices.state import StoredDeviceState


class ApiMessage(Serializable):
    def __init__(self,
                 base_url: str,
                 method: str,
                 token: str):
        self.endpoint = self.get_endpoint(
            base_url=base_url)

        self.method = method
        self.json = self.get_body()
        self.headers = self.get_headers(
            token=token)

    def get_delay(_timedelta):
        return None

    def get_body(self) -> dict:
        pass

    def get_endpoint(self, base_url) -> str:
        pass

    def get_headers(self, token) -> str:
        return {
            'Authorization': f'Bearer {token}'
        }

    def to_service_bus_message(self) -> ServiceBusMessage:
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


class StoreDeviceStateEvent(ApiMessage):
    def __init__(
            self,
            device_state: StoredDeviceState,
            base_url: str,
            auth_token: str):

        self.device_state = device_state
        super().__init__(
            base_url,
            'POST',
            auth_token)

    def get_delay(_timedelta):
        return timedelta(seconds=3)

    def get_body(self) -> dict:
        return self.device_state.to_request()

    def get_endpoint(self, base_url) -> str:
        return f'{base_url}/api/device/state'
