from framework.exceptions.nulls import ArgumentNullException
from framework.logger import get_logger
from framework.validators.nulls import none_or_whitespace
from clients.event_client import EventClient

from data.repositories.kasa_device_state_repository import \
    KasaDeviceStateRepository
from domain.exceptions import InvalidDeviceException, InvalidPresetException
from domain.kasa.devices.state import KasaDeviceState

logger = get_logger(__name__)


class KasaDeviceStateService:
    def __init__(
        self,
        state_repository: KasaDeviceStateRepository,
        event_client: EventClient
    ):
        self.__state_repository = state_repository
        self.__event_client = event_client

    async def set_device_state(
        self,
        request_device_state: KasaDeviceState
    ):
        ArgumentNullException.if_none(
            request_device_state, 'device_state')

        if none_or_whitespace(request_device_state.device_id):
            raise InvalidDeviceException(
                device_id=request_device_state.device_id)

        if none_or_whitespace(request_device_state.preset_id):
            raise InvalidPresetException(
                preset_id=request_device_state.preset_id)

        logger.info(f'Set device state: {request_device_state.to_dict()}')

        # Fetch the existing device state record if it exists
        entity = await self.__state_repository.get({
            'device_id': existing_device_state.device_id
        })

        if entity is None:
            logger.info('Creating initial device state')
            await self.__state_repository.insert(
                document=request_device_state.to_dict())

            return request_device_state

        logger.info('Updating existing device state')
        existing_device_state = KasaDeviceState.from_entity(
            data=entity)

        # Update the existing device state record
        request_device_state.update_device_state(
            device_state=request_device_state)

        await self.__state_repository.replace(
            selector=existing_device_state.get_selector(),
            document=existing_device_state.to_dict())

        return existing_device_state

    async def get_device_state(
        self,
        device_id: str
    ):
        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')

        entity = await self.__state_repository.get({
            'device_id': device_id
        })

        # Return none if no stored device
        # state exists
        if entity is None:
            return

        device_state = KasaDeviceState.from_entity(
            data=entity)

        return device_state
