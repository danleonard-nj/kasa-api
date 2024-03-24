from typing import Dict

from domain.rest import SetDevicePresetResponse, UpdateDeviceRequest
from framework.concurrency import TaskCollection
from framework.exceptions.nulls import ArgumentNullException
from framework.logger import get_logger
from services.kasa_device_service import KasaDeviceService
from services.kasa_preset_service import KasaPresetSevice
from framework.exceptions.nulls import ArgumentNullException

from utils.helpers import DateTimeUtil

logger = get_logger(__name__)


class KasaDeviceProvider:
    def __init__(
        self,
        device_service: KasaDeviceService
    ):
        self._device_service = device_service

    async def get_device_logs(
        self,
        start_date: str,
        end_date: str
    ):
        '''
        Handle get device logs request
        '''

        ArgumentNullException.if_none_or_whitespace(start_date, 'start_date')

        logger.info(f'Start date: {start_date}')
        logger.info(f'End date: {end_date}')

        parsed_start_date = DateTimeUtil.parse(start_date)

        # Use the current date if end date is not provided
        parsed_end_date = (
            DateTimeUtil.parse(end_date)
            if end_date is not None
            else DateTimeUtil.now()
        )

        logger.info(f'Parsed start date: {parsed_start_date}')
        logger.info(f'Parsed end date: {parsed_end_date}')

        return await self._device_service.get_device_logs(
            start_timestamp=int(parsed_start_date.timestamp()),
            end_timestamp=int(parsed_end_date.timestamp()))

    async def get_all_devices(
        self
    ):
        '''
        Handle get all devices request
        '''

        return await self._device_service.get_all_devices()

    async def update_device(
        self,
        body: Dict
    ):
        '''
        Handle device update request
        '''

        ArgumentNullException.if_none(body, 'body')

        update_request = UpdateDeviceRequest(
            data=body)

        return await self._device_service.update_device(
            update_request=update_request)

    async def get_device(
        self,
        device_id: str
    ):
        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')

        return await self._device_service.get_device(
            device_id=device_id)

    async def set_device_region(
        self,
        device_id: str,
        region_id: str
    ):
        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')
        ArgumentNullException.if_none_or_whitespace(region_id, 'region_id')

        return await self._device_service.set_device_region(
            device_id=device_id,
            region_id=region_id)

    async def sync_devices(
        self,
        destructive: str
    ):
        is_destructive = destructive == 'true'

        return await self._device_service.sync_devices(
            destructive=is_destructive)

    async def get_device_client_response(
        self,
        device_id: str
    ):
        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')

        return await self._device_service.get_device_client_response(
            device_id=device_id)

    async def get_device_state(
        self,
        device_id
    ):
        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')

        device = await self._device_service.get_device_state(
            device_id=device_id)

        return device.device_object

    async def set_device_preset(
        self,
        device_id: str,
        preset_id: str
    ):
        '''
        Handle set device preset request
        '''

        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')
        ArgumentNullException.if_none_or_whitespace(preset_id, 'preset_id')

        logger.info(f'Device: {device_id}: Preset: {preset_id}')

        get_device_presets = TaskCollection(
            self._device_service.get_device(
                device_id=device_id),
            self.__preset_service.get_preset(
                preset_id=preset_id))

        device, preset = await get_device_presets.run()

        kasa_request, kasa_response = await self._device_service.set_device_state(
            device=device,
            preset=preset)

        response = SetDevicePresetResponse(
            kasa_request=kasa_request,
            kasa_response=kasa_response)

        return response
