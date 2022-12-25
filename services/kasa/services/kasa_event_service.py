from queue import Queue

from framework.clients.cache_client import CacheClientAsync
from framework.configuration import Configuration
from framework.logger import get_logger
from framework.validators.nulls import none_or_whitespace

from clients.identity_client import IdentityClient
from clients.service_bus import EventClient
from domain.cache import CacheKey
from domain.events import StoreKasaClientResponseEvent

logger = get_logger(__name__)


class KasaEventService:
    def __init__(
        self,
        configuration: Configuration,
        queue_client: EventClient,
        cache_client: CacheClientAsync,
        identity_client: IdentityClient
    ):
        self.__queue_client = queue_client
        self.__cache_client = cache_client
        self.__identity_client = identity_client

        self.__configuration = configuration
        self.__base_url = self.__configuration.events.get('base_url')

    async def __get_client_token(
        self
    ) -> str:
        '''
        Fetch a client token scoped to 'execute' for
        service bus messages
        '''

        cached_token = await self.__cache_client.get_cache(
            key=CacheKey.event_token())

        if cached_token is not None:
            logger.info(f'Returning cached event token')
            return cached_token

        logger.info(f'Fetching event token')
        token = await self.__identity_client.get_token(
            client_name='kasa-api')

        if none_or_whitespace(token):
            raise Exception('Event token cannot be null')

        return token

    async def refresh_token(
        self
    ):
        logger.info(f'Refreshing token')
        await self.__get_client_token()

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

        token = await self.__get_client_token()

        event = StoreKasaClientResponseEvent(
            kasa_response=client_response,
            device_id=device_id,
            preset_id=preset_id,
            state_key=state_key,
            base_url=self.__base_url,
            token=token)

        logger.info(
            f'{preset_id}: {device_id}: Client response event dispatched')

        await self.__queue_client.send_message(
            message=event.to_service_bus_message())

        logger.info(f'{preset_id}: {device_id}: Client response event sent')
