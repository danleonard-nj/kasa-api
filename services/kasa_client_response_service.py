from typing import Dict

from framework.logger import get_logger

from data.repositories.kasa_client_response_repository import \
    KasaClientResponseRepository
from domain.exceptions import NullArgumentException
from domain.kasa.client_response import KasaClientResponse
from domain.rest import UpdateClientResponseRequest
from domain.sync import SyncStatusReason

logger = get_logger(__name__)


class KasaClientResponseService:
    def __init__(
        self,
        client_response_repository: KasaClientResponseRepository
    ):
        self.__client_response_repository = client_response_repository

    def __handle_sync_status_update(
        self,
        model: KasaClientResponse
    ) -> KasaClientResponse:

        # Update the sync status to out of sync if the client
        # returns an error status (usually device is not live
        # or reachable i.e. device was turned off manually)
        if model.is_error:
            model.update_sync_status(
                sync_status=False,
                sync_reason=SyncStatusReason.ClientResponseError)

        # Sync status true if client returns success
        else:
            model.update_sync_status(
                sync_status=True,
                sync_reason=SyncStatusReason.ClientResponseSuccess)

        return model

    async def update_client_response(
        self,
        request: UpdateClientResponseRequest
    ) -> Dict:
        '''
        Update client response record for a given
        device
        '''

        NullArgumentException.if_none_or_whitespace(
            request.device_id, 'device_id')
        NullArgumentException.if_none(
            request.client_response, 'client_response')

        logger.info(f'Update client response for device: {request.device_id}')

        entity = await self.__client_response_repository.get({
            'device_id': request.device_id
        })

        if entity is None:
            return await self.create_client_response(
                device_id=request.device_id,
                preset_id=request.preset_id,
                client_response=request.client_response,
                state_key=request.state_key)

        model = KasaClientResponse(
            data=entity)

        # Update the client response
        model.update_client_response(
            request=request)

        # Set the device sync status
        model = self.__handle_sync_status_update(
            model=model)

        # Update the record
        result = await self.__client_response_repository.update(
            model.get_selector(),
            model.to_dict())

        logger.info(f'Updated records: {result.acknowledged}')
        return model

    async def create_client_response(
        self,
        device_id: str,
        preset_id: str,
        client_response: Dict,
        state_key: str
    ) -> Dict:
        '''
        Create a client response for a given device
        '''

        logger.info(f'Create client response record')

        model = KasaClientResponse.create_client_response(
            device_id=device_id,
            preset_id=preset_id,
            client_response=client_response,
            state_key=state_key)

        model = self.__handle_sync_status_update(
            model=model)

        await self.__client_response_repository.insert(
            model.to_dict())

        return model.to_dict()

    async def get_client_response(
        self,
        device_id: str
    ) -> KasaClientResponse:
        '''
        Get the client response record for a given device
        '''

        entity = await self.__client_response_repository.get({
            'device_id': device_id
        })

        if entity is None:
            raise Exception(
                f"No client response found for device with the ID '{device_id}'")

        return KasaClientResponse(
            data=entity)
