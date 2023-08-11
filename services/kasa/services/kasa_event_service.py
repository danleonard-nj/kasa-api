from framework.configuration import Configuration
from framework.logger import get_logger

from clients.event_client import EventClient
from clients.identity_client import IdentityClient
from domain.events import StoreKasaClientResponseEvent

logger = get_logger(__name__)


class KasaClientResponseEventException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class KasaEventService:
    def __init__(
        self,
        configuration: Configuration,
        queue_client: EventClient,
        identity_client: IdentityClient
    ):
        self.__queue_client = queue_client
        self.__identity_client = identity_client

        self.__configuration = configuration
        self.__base_url = self.__configuration.events.get('base_url')

    async def send_client_response_event(
        self,
        device_id: str,
        preset_id: str,
        client_response: dict,
        state_key: str
    ) -> None:
        '''
        Dispatch a client response event to store
        the Kasa client response and the current
        preset for a given device
        '''

        logger.info(
            f'{preset_id}: {device_id}: Dispatching client response event')

        logger.info(f'Fetching event token')
        token = await self.__identity_client.get_token(
            client_name='kasa-api')

        event = StoreKasaClientResponseEvent(
            kasa_response=client_response,
            device_id=device_id,
            preset_id=preset_id,
            state_key=state_key,
            base_url=self.__base_url,
            token=token)

        logger.info(f'Client response event: {event.to_dict()}')

        self.__queue_client.send_message(
            message=event.to_service_bus_message())

        logger.info(f'{preset_id}: {device_id}: Client response event sent')
