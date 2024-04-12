import asyncio
from domain.cache import CacheKey
from domain.rest import (GetDevicesRequest, GetKasaDeviceStateRequest,
                         KasaGetDevicesResponse, KasaResponse,
                         KasaTokenRequest, KasaTokenResponse)
from framework.clients.cache_client import CacheClientAsync
from framework.configuration.configuration import Configuration
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger
from framework.validators.nulls import none_or_whitespace
from httpx import AsyncClient
from utils.helpers import fire_task

logger = get_logger(__name__)

semaphore = asyncio.Semaphore(24)


class KasaClient:
    def __init__(
        self,
        configuration: Configuration,
        cache_client: CacheClientAsync,
        http_client: AsyncClient
    ):
        self._cache_client = cache_client

        self._username = configuration.kasa.get('username')
        self._password = configuration.kasa.get('password')
        self._base_url = configuration.kasa.get('base_url')

        self._http_client = http_client

        ArgumentNullException.if_none_or_whitespace(
            self._username, 'username')
        ArgumentNullException.if_none_or_whitespace(
            self._password, 'password')
        ArgumentNullException.if_none_or_whitespace(
            self._base_url, 'base_url')

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

        return await self._send_request(
            json=data)

    async def set_device_state(
        self,
        kasa_request: dict,
        kasa_token: str = None,
        max_retries: int = 3
    ) -> KasaResponse:
        '''
        Set the Kasa device state
        '''

        ArgumentNullException.if_none(kasa_request, 'kasa_request')

        logger.info(f'Sending device state request to Kasa client')

        for _ in range(max_retries):
            try:
                return await self._send_request(
                    json=kasa_request,
                    kasa_token=kasa_token)
            except Exception as e:
                logger.info(f'Attempt to set device state failed: {e}')
                continue

        # If we've reached this point we've failed to set the device state
        raise Exception(f'Failed to set device state: {kasa_request}')

    async def get_devices(
        self
    ) -> KasaGetDevicesResponse:
        '''
        Get a list of the Kasa devices
        '''

        logger.info(f'Fetching devices from Kasa client')
        request = GetDevicesRequest()

        content = await self._send_request(
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
        cached_token = await self._cache_client.get_cache(
            key=CacheKey.kasa_token())

        if not none_or_whitespace(cached_token):
            logger.info(f'Returning cached Kasa token')
            return cached_token

        token_response = await self._fetch_kasa_token_from_client()

        if token_response.is_error:
            raise Exception(f'Failed to fetch Kasa auth token: {token_response.error_message}')

        # Cache the token for 30 mins
        fire_task(
            self._cache_client.set_cache(
                key=CacheKey.kasa_token(),
                value=token_response.token,
                ttl=30))

        return token_response.token

    async def _send_request(
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

        await semaphore.acquire()

        try:
            response = await self._http_client.post(
                url=f'{self._base_url}/?token={kasa_token}',
                json=json)
        except Exception as e:
            logger.info(f'Failed to send request: {str(e)}')
            raise e
        finally:
            semaphore.release()

        response = KasaResponse(
            response=response)

        if response.is_error:
            logger.error(f'Failed to send Kasa request: {response.response.status_code}: {response.data}')

        return response

    async def _fetch_kasa_token_from_client(
        self
    ) -> KasaTokenResponse:
        ''''
        Fetch an auth token from the Kasa client
        '''

        logger.info(f'Fetching Kasa token from client')
        request = KasaTokenRequest(
            username=self._username,
            password=self._password).to_dict()

        try:
            response = await self._http_client.post(
                url=f'{self._base_url}/',
                json=request)

            content = response.json()
            logger.info(f'Kasa token response: {content}')

            return KasaTokenResponse(
                response=response)

        except Exception as e:
            logger.exception(f'Failed to fetch Kasa token: {e}')
            raise e
