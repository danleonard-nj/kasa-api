import asyncio
from typing import List
from framework.clients.cache_client import CacheClientAsync
from framework.configuration import Configuration
from framework.logger import get_logger
from framework.validators.nulls import none_or_whitespace

from clients.identity_client import IdentityClient
from clients.event_client import EventClient
from domain.cache import CacheKey
from domain.events import SetDeviceStateEvent, StoreKasaClientResponseEvent
from domain.rest import SetDeviceStateRequest

logger = get_logger(__name__)


class KasaClientResponseEventException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


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

        # If we don't get the token back
        if none_or_whitespace(token):
            raise KasaClientResponseEventException(
                'Failed to fetch event token for client response event')

        # Cache the fetched token
        asyncio.create_task(self.__cache_client.set_cache(
            key=CacheKey.event_token(),
            value=token))

        return token

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

        token = await self.__get_client_token()

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

    # async def dispatch_device_state_update_events(
    #     self,
    #     update_requests: List[SetDeviceStateRequest]
    # ):
    #     logger.info(f'Dispatching update state requests')

    #     token = await self.__get_client_token()

    #     # Create device state update events
    #     update_events = [
    #         SetDeviceStateEvent(
    #             body=update_request,
    #             base_url=self.__base_url,
    #             token=token)
    #         for update_request in update_requests
    #     ]

    #     # Create service bus messages from event messages
    #     event_messages = [update_event.to_service_bus_message()
    #                       for update_event in update_events]

    #     # Send message batch
    #     self.__queue_client.send_messages(
    #         messages=event_messages)
    #     logger.info(f'Service bus message batch sent')
