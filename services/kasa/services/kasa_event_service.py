from clients.event_client import EventClient
from clients.identity_client import IdentityClient
from domain.events import StoreKasaClientResponseEvent
from framework.configuration import Configuration
from framework.exceptions.nulls import ArgumentNullException
from framework.logger import get_logger

logger = get_logger(__name__)


class KasaEventService:
    def __init__(
        self,
        configuration: Configuration,
        queue_client: EventClient,
        identity_client: IdentityClient
    ):
        self._queue_client = queue_client
        self._identity_client = identity_client

        self._configuration = configuration
        self._base_url = self._configuration.events.get('base_url')

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

        ArgumentNullException.if_none_or_whitespace(
            device_id, 'device_id')
        ArgumentNullException.if_none_or_whitespace(
            preset_id, 'preset_id')
        ArgumentNullException.if_none(
            client_response, 'client_response')
        ArgumentNullException.if_none_or_whitespace(
            state_key, 'state_key')

        logger.info(
            f'{preset_id}: {device_id}: Dispatching client response event')

        logger.info(f'Fetching event token')
        token = await self._identity_client.get_token(
            client_name='kasa-api')

        event = StoreKasaClientResponseEvent(
            kasa_response=client_response,
            device_id=device_id,
            preset_id=preset_id,
            state_key=state_key,
            base_url=self._base_url,
            token=token)

        logger.info(f'Client response event: {event.to_dict()}')

        self._queue_client.send_message(
            message=event.to_service_bus_message())

        logger.info(f'{preset_id}: {device_id}: Client response event sent')
