from framework.clients.cache_client import CacheClientAsync
from framework.clients.http_client import HttpClient
from framework.configuration.configuration import Configuration
from framework.constants.constants import ConfigurationKey
from framework.logger.providers import get_logger
from framework.serialization.utilities import serialize
from framework.validators.nulls import none_or_whitespace, not_none

from domain.cache import CacheKey

logger = get_logger(__name__)


class IdentityClient:
    def __init__(
        self,
        configuration: Configuration,
        cache_client: CacheClientAsync
    ):
        not_none(configuration, 'configuration')

        self.__ad_auth = configuration.ad_auth
        self.__cache_client = cache_client
        self.__http_client = HttpClient()

        logger.info('Configuring identity client')
        self.__clients = dict()

        logger.info('Loading identity clients from configuration')
        for client in self.__ad_auth.clients:
            self.__add_client(client)

    def __add_client(
        self,
        config: dict
    ) -> None:

        scopes = config.get(ConfigurationKey.CLIENT_SCOPE)
        client_name = config.get(
            'name')

        client_config = {
            'client_id': config.get(
                ConfigurationKey.CLIENT_CLIENT_ID),
            'client_secret': config.get(
                ConfigurationKey.CLIENT_CLIENT_SECRET),
            'grant_type': config.get(
                ConfigurationKey.CLIENT_GRANT_TYPE),
            'scope': ' '.join(scopes)
        }

        self.__clients.update({
            client_name: client_config
        })

    # def __get_client(
    #     self,
    #     client_name: str
    # ):
    #     if not self.__clients.get(client_name):
    #         raise Exception(f'No client with the name {client_name} exists')

    #     return self.__clients.get(client_name)

    async def get_token(
        self,
        client_name: str
    ):
        cached_token = await self.__cache_client.get_cache(
            key=CacheKey.auth_token(client_name))

        if not none_or_whitespace(cached_token):
            logger.info(f'Auth client: {client_name}: Returning cached token')
            return cached_token

        client = self.__clients.get(client_name)

        if client is None:
            raise Exception(f'No client exists with the name {client_name}')

        logger.info(f'Client: {serialize(client)}')

        response = await self.__http_client.post(
            url=f'{self.__ad_auth.identity_url}',
            data=client,
            headers={
                'ContentType': 'application/json'
            })

        logger.info(f'Response: {response.status_code}')

        if response.status_code != 200:
            raise Exception(
                f'Failed to fetch auth token: {response.status_code}: {response.text}')

        token = response.json().get(
            'access_token')

        await self.__cache_client.set_cache(
            key=CacheKey.auth_token(client_name),
            value=token,
            ttl=60)

        return token
