from typing import Dict
from services.kasa_device_state_service import KasaDeviceStateService
from domain.rest import SetDeviceStateRequest
from domain.kasa.devices.state import KasaDeviceState
from framework.logger import get_logger

logger = get_logger(__name__)


class KasaDeviceStateProvider:
    def __init__(
        self,
        device_state_service: KasaDeviceStateService
    ):
        self.__device_state_service = device_state_service

    async def set_device_state(
        self,
        body: Dict
    ):
        update_request = SetDeviceStateRequest(
            data=body)

        logger.info(f'Set device state: {update_request.device_id}')

        device_state = KasaDeviceState.create_device_state(
            device_id=update_request.device_id,
            preset_id=update_request.preset_id,
            state_key=update_request.state_key,
            power_state=update_request.power_state)

        await self.__device_state_service.set_device_state(
            existing_device_state=device_state)

    async def get_device_state(
        self,
        device_id: str
    ):
        logger.info(f'Get device state: {device_id}')

        device_state = await self.__device_state_service.get_device_state(
            device_id=device_id)

        return device_state
