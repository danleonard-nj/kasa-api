from framework.clients.cache_client import CacheClientAsync
from framework.configuration.configuration import Configuration
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger
from framework.validators.nulls import none_or_whitespace
from httpx import AsyncClient

from domain.cache import CacheKey
from domain.rest import (GetDevicesRequest, GetKasaDeviceStateRequest,
                         KasaGetDevicesResponse, KasaResponse,
                         KasaTokenRequest, KasaTokenResponse)
from services.kasa_event_service import KasaEventService

logger = get_logger(__name__)


class KasaClient:
    def __init__(
        self,
        configuration: Configuration,
        http_client: AsyncClient,
        cache_client: CacheClientAsync,
        event_service: KasaEventService
    ):
        self.__cache_client = cache_client
        self.__http_client = http_client

        self.__username = configuration.kasa.get('username')
        self.__password = configuration.kasa.get('password')
        self.__base_url = configuration.kasa.get('base_url')

        ArgumentNullException.if_none_or_whitespace(
            self.__username, 'username')
        ArgumentNullException.if_none_or_whitespace(
            self.__password, 'password')
        ArgumentNullException.if_none_or_whitespace(
            self.__base_url, 'base_url')

    async def get_device_state(
        self,
        device_id: str
    ) -> KasaResponse:
        '''
        Get the current device state
        '''

        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')

        request = GetKasaDeviceStateRequest(
            device_id=device_id)

        data = request.to_dict()
        logger.info(f'Device state request: {data}')

        return await self.__send_request(
            json=data)

    async def set_device_state(
        self,
        kasa_request: dict,
        kasa_token: str = None
    ) -> KasaResponse:
        '''
        Set the Kasa device state
        '''

        ArgumentNullException.if_none(kasa_request, 'kasa_request')

        logger.info(f'Sending device state request to Kasa client')
        response = await self.__send_request(
            json=kasa_request,
            kasa_token=kasa_token)

        return response

    async def get_devices(
        self
    ) -> KasaGetDevicesResponse:
        '''
        Get a list of the Kasa devices
        '''

        logger.info(f'Fetching devices from Kasa client')
        request = GetDevicesRequest()

        content = await self.__send_request(
            json=request.to_dict())

        response = KasaGetDevicesResponse(
            data=content)

        return response

    async def get_kasa_token(
        self
    ) -> str:
        ''' 
        Fetch a Kasa token from cache if availabl
        otherwise fetch it from the Kasa client
        '''

        logger.info(f'Fetching Kasa token from cache')
        cached_token = await self.__cache_client.get_cache(
            key=CacheKey.kasa_token())

        if cached_token is not None:
            logger.info(f'Returning cached Kasa token')
            return cached_token

        token_response = await self.__fetch_kasa_token_from_client()

        if token_response.is_error:
            raise Exception(
                f'Failed to fetch Kasa auth token: {token_response.error_message}')

        logger.info(f'Kasa token: {token_response}')

        await self.__cache_client.set_cache(
            key=CacheKey.kasa_token(),
            value=token_response.token,
            ttl=60 * 6)

        return token_response.token

    async def __send_request(
        self,
        json: dict,
        kasa_token: str = None
    ) -> KasaResponse:
        '''
        Send a request to the Kasa client
        '''

        ArgumentNullException.if_none(json, 'json')

        # Only grab the token if we haven't passed it
        # down from top level
        if none_or_whitespace(kasa_token):
            kasa_token = await self.get_kasa_token()

        response = await self.__http_client.post(
            url=f'{self.__base_url}/?token={kasa_token}',
            json=json,
            timeout=None)

        logger.info(f'Status: {response.status_code}')

        response = KasaResponse(
            data=response.json())

        if response.is_error:
            logger.error(f'Failed to send request: {response.error_message}')

        return response

    async def __fetch_kasa_token_from_client(
        self
    ) -> KasaTokenResponse:
        ''''
        Fetch an auth token from the Kasa client
        '''

        logger.info(f'Fetching Kasa token from client')
        request = KasaTokenRequest(
            username=self.__username,
            password=self.__password).to_dict()

        response = await self.__http_client.post(
            url=f'{self.__base_url}/',
            json=request)

        content = response.json()
        logger.info(f'Kasa token response: {content}')

        return KasaTokenResponse(
            data=content)

    async def refresh_token(
        self
    ) -> str:
        '''
        Refresh the Kasa token if the cached token
        is expired.  This can be called proactively
        before concurrent calls to the Kasa client
        to prevent multiple calls fetching the token
        before the first call is cached
        '''

        cached_token = await self.__cache_client.get_cache(
            key=CacheKey.kasa_token())

        if cached_token is None:
            logger.info(f'Refreshing Kasa client token')

            token = await self.get_kasa_token()
            logger.info(f'Token: {token}')
        else:
            logger.info('Kasa client token is valid')
