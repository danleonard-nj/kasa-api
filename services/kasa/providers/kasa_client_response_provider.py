from typing import Dict

from framework.exceptions.nulls import ArgumentNullException
from framework.logger import get_logger

from domain.kasa.client_response import KasaClientResponse
from domain.rest import UpdateClientResponseRequest
from services.kasa_client_response_service import KasaClientResponseService

logger = get_logger(__name__)


class KasaClientResponseProvider:
    def __init__(
        self,
        kasa_client_response_service: KasaClientResponseService
    ):
        self.__kasa_client_response_service = kasa_client_response_service

    async def create_client_response(
        self,
        device_id: str,
        preset_id: str,
        client_response: Dict
    ) -> Dict:

        ArgumentNullException.if_none(client_response, 'client_response')
        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')
        ArgumentNullException.if_none_or_whitespace(preset_id, 'preset_id')

        logger.info(f'Create client response: {client_response}')

        response = await self.__kasa_client_response_service.create_client_response(
            device_id=device_id,
            preset_id=preset_id,
            client_response=client_response)

        return response

    async def update_client_response(
        self,
        body: Dict
    ) -> Dict:

        ArgumentNullException.if_none(body, 'body')
        request = UpdateClientResponseRequest(
            data=body)

        logger.info(f'Update client response: {request.device_id}')

        result = await self.__kasa_client_response_service.update_client_response(
            request=request)

        return result

    async def get_client_response(
        self,
        device_id: str
    ) -> KasaClientResponse:

        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')
        logger.info(f'Get device: {device_id}')

        client_response = await self.__kasa_client_response_service.get_client_response(
            device_id=device_id)

        return client_response.to_dict()
