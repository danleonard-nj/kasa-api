from typing import Dict

from framework.logger import get_logger

from domain.rest import SetDevicePresetResponse, UpdateDeviceRequest
from framework.concurrency import TaskCollection
from services.kasa_device_service import KasaDeviceService
from framework.exceptions.nulls import ArgumentNullException

from services.kasa_preset_service import KasaPresetSevice

logger = get_logger(__name__)


class KasaDeviceProvider:
    def __init__(
        self,
        device_service: KasaDeviceService,
        preset_service: KasaPresetSevice
    ):
        self.__device_service = device_service
        self.__preset_service = preset_service

    async def get_all_devices(
        self
    ):
        '''
        Handle get all devices request
        '''

        return await self.__device_service.get_all_devices()

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

        return await self.__device_service.update_device(
            update_request=update_request)

    async def get_device(
        self,
        device_id: str
    ):
        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')

        return await self.__device_service.get_device(
            device_id=device_id)

    async def set_device_region(
        self,
        device_id: str,
        region_id: str
    ):
        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')
        ArgumentNullException.if_none_or_whitespace(region_id, 'region_id')

        return await self.__device_service.set_device_region(
            device_id=device_id,
            region_id=region_id)

    async def sync_devices(
        self,
        destructive: str
    ):
        is_destructive = destructive == 'true'

        return await self.__device_service.sync_devices(
            destructive=is_destructive)

    async def get_device_client_response(
        self,
        device_id: str
    ):
        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')

        return await self.__device_service.get_device_client_response(
            device_id=device_id)

    async def get_device_state(
        self,
        device_id
    ):
        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')

        device = await self.__device_service.get_device_state(
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
            self.__device_service.get_device(
                device_id=device_id),
            self.__preset_service.get_preset(
                preset_id=preset_id))

        device, preset = await get_device_presets.run()

        kasa_request, kasa_response = await self.__device_service.set_device_state(
            device=device,
            preset=preset)

        response = SetDevicePresetResponse(
            kasa_request=kasa_request,
            kasa_response=kasa_response)

        return response
