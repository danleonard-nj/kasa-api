from typing import Dict, List, Tuple

from deprecated import deprecated
from clients.cache_client import CacheClientAsync
from framework.concurrency import TaskCollection
from framework.logger.providers import get_logger
from framework.validators.nulls import none_or_whitespace

from clients.kasa_client import KasaClient
from data.repositories.kasa_device_repository import KasaDeviceRepository
from domain.cache import CacheExpiration, CacheKey
from domain.exceptions import (DeviceNotFoundException,
                               InvalidDeviceRequestException,
                               NoDevicesDefinedForRegionException,
                               NullArgumentException, RegionNotFoundException)
from domain.kasa.device import KasaDevice
from domain.kasa.preset import KasaPreset
from domain.rest import KasaRequest, KasaResponse, UpdateDeviceRequest
from services.kasa_client_response_service import KasaClientResponseService
from services.kasa_region_service import KasaRegionService

logger = get_logger(__name__)


class KasaDeviceService:
    def __init__(
        self,
        kasa_client: KasaClient,
        device_repository: KasaDeviceRepository,
        region_service: KasaRegionService,
        cache_client: CacheClientAsync,
        client_response_service: KasaClientResponseService
    ):
        self.__kasa_client = kasa_client
        self.__device_repository = device_repository
        self.__region_service = region_service
        self.__cache_client = cache_client
        self.__client_response_service = client_response_service

    async def expire_cached_device(
        self,
        device_id: str
    ) -> None:
        '''
        Expire a caced device
        '''

        logger.info(f'Expire cached device: {device_id}')

        await self.__cache_client.delete_key(
            key=CacheKey.device_key(
                device_id=device_id))

    async def expire_cached_device_list(
        self
    ) -> None:
        '''
        Expire the cached device list
        '''

        logger.info(f'Expire cached device list')

        await self.__cache_client.delete_key(
            key=CacheKey.device_list())

    async def get_device(
        self,
        device_id: str
    ) -> KasaDevice:
        '''
        Get a device
        '''

        logger.info(f'Get device: {device_id}')

        device = await self.__cache_client.get_json(
            key=CacheKey.device_key(
                device_id=device_id))

        if device is None:
            device = await self.__device_repository.get({
                'device_id': device_id
            })

            await self.__cache_client.set_json(
                key=CacheKey.device_key(
                    device_id=device_id),
                value=device,
                ttl=CacheExpiration.days(7))

        if device is None:
            raise DeviceNotFoundException(
                device_id=device_id)

        kasa_device = KasaDevice(
            data=device)

        return kasa_device

    async def get_all_devices(
        self
    ) -> list[KasaDevice]:
        '''
        Get device list
        '''

        logger.info('Get all devices')
        device_entities = await self.__cache_client.get_json(
            key=CacheKey.device_list())

        if device_entities is None:
            device_entities = await self.__device_repository.get_all()

            await self.__cache_client.set_json(
                key=CacheKey.device_list(),
                ttl=CacheExpiration.days(7),
                value=device_entities)

        logger.info(f'Fetched {len(device_entities)} devices')
        kasa_devices = [KasaDevice(device)
                        for device in device_entities]

        return kasa_devices

    @deprecated
    async def sync_devices(
        self
    ):
        logger.info('Syncing devices')

        await self.expire_cached_device_list()
        logger.info('Fetching devices from client')

        get_devices = TaskCollection(
            self.__kasa_client.get_devices(),
            self.__device_repository.get_all())

        devices, device_entities = await get_devices.run()

        known_device_ids = [KasaDevice(data=entity).device_id
                            for entity in device_entities]

        created_devices = []
        for device in devices.device_list:
            logger.info(device)

            device_id = device.get('deviceId')
            logger.info(f'{device_id}: Syncing device')

            # Verify we have the device synced by the
            # Kasa device ID
            if device_id not in known_device_ids:
                logger.info(f'{device_id}: Creating device')

                # Create the device if it's not known
                created_devices.append(device)

            else:
                logger.info(f'{device_id}: Known device')

        if any(created_devices):
            logger.info(f'Creating {len(created_devices)} new devices')

            create_devices = TaskCollection([
                self.__create_kasa_device(client_device=device)
                for device in created_devices
            ])

            await create_devices.run()

        return created_devices

    async def __create_kasa_device(
        self,
        client_device: Dict
    ) -> None:

        kasa_device = KasaDevice.from_kasa_device_params(
            data=client_device)

        await self.__device_repository.insert(
            document=kasa_device.to_dict())

    async def set_device_state(
        self,
        device: KasaDevice,
        preset: KasaPreset
    ) -> Tuple[KasaRequest, KasaResponse]:
        '''
        Set a device state to a given preset
        '''

        NullArgumentException.if_none(device, 'device')
        NullArgumentException.if_none(preset, 'preset')

        logger.info(
            f'Set device state: {device.device_id}: Preset: {preset.preset_id}')

        # Fetch the Kasa client request from cache if we have it
        kasa_request = await self.__cache_client.get_json(
            key=CacheKey.kasa_request(
                preset_id=preset.preset_id,
                device_id=device.device_id))

        if kasa_request is None:
            kasa_request = preset.to_request(
                device=device).get_request_body()

        logger.info(f'Sending Kasa device state request')

        # Run Kasa client commands
        client_results = await self.__kasa_client.set_device_state(
            kasa_request=kasa_request,
            device_id=device.device_id,
            preset_id=preset.preset_id)

        # TODO: Clear this up, do these cases actually happen?
        if isinstance(client_results, list):
            response = [res.to_dict()
                        for res in client_results]
        else:
            response = client_results.to_dict()

        return (kasa_request, response)

    async def update_device(
        self,
        update_request: UpdateDeviceRequest
    ) -> KasaDevice:
        '''
        Update a known Kasa device
        '''

        NullArgumentException.if_none(update_request, 'update_request')

        logger.info(f'Update device: {update_request.to_dict()}')

        # Expire cached device list and cached device that
        # we're updating heres
        clear_cache = TaskCollection(
            self.expire_cached_device(
                device_id=update_request.device_id),
            self.expire_cached_device_list())

        await clear_cache.run()

        if none_or_whitespace(update_request.device_id):
            raise InvalidDeviceRequestException('No device ID was provided')

        device = await self.get_device(
            device_id=update_request.device_id)

        # TODO: Move update logic into device class
        device.device_name = update_request.device_name
        device.device_type = update_request.device_type
        device.region_id = update_request.region_id

        logger.info(f'Updated device: {device.to_dict()}')

        await self.__device_repository.update(
            selector=device.get_selector(),
            values=device.to_dict())

        return device

    async def set_device_region(
        self,
        device_id: str,
        region_id: str
    ) -> KasaDevice:
        '''
        Associate a known Kasa device to a
        device region
        '''

        # Expire cached device and device list

        NullArgumentException.if_none_or_whitespace(region_id, 'region_id')
        NullArgumentException.if_none_or_whitespace(device_id, 'device_id')

        # Expire cached device list
        expirations = TaskCollection(
            self.expire_cached_device(
                device_id=device_id),
            self.expire_cached_device_list())
        await expirations.run()

        logger.info(f'Set device region: {device_id}: {region_id}')

        fetch = TaskCollection(
            self.__region_service.get_region(
                region_id=region_id),
            self.__device_repository.get({
                'device_id': device_id
            }))

        region, entity = await fetch.run()

        # Verify provided device exists
        if entity is None:
            raise DeviceNotFoundException(
                device_id=device_id)

        # Verify provided region exists
        if region is None:
            raise RegionNotFoundException(
                region_id=region_id)

        device = KasaDevice(
            data=entity)

        device.set_region(
            region_id=region_id)

        logger.info(
            f'Updating device: {device.device_name} to region: {region.region_name}')

        update_result = await self.__device_repository.replace(
            selector=device.get_selector(),
            document=device.to_dict())

        logger.info(f'Update result: {update_result.modified_count}')
        return device

    async def get_device_client_response(
        self,
        device_id: str
    ) -> Dict:
        '''
        Get the stored client response for a
        known Kasa device

        `device_id`: Kasa device ID
        '''

        NullArgumentException.if_none_or_whitespace(device_id, 'device_id')

        client_response = await self.__client_response_service.get_client_response(
            device_id=device_id)

        if client_response is None:
            raise Exception('No client response exists for device')

        return client_response.to_dict()

    async def get_devices(
        self,
        device_ids: List[str],
        region_id: str = None
    ):
        '''
        Get devices from a list of device IDs
        '''

        NullArgumentException.if_none(device_ids, 'device_ids')

        entities = await self.__device_repository.get_devices(
            device_ids=device_ids,
            region_id=region_id)

        devices = [KasaDevice(data=entity)
                   for entity in entities]

        return devices

    async def clear_cache_by_region(
        self,
        region_id: str
    ):
        NullArgumentException.if_none_or_whitespace(
            region_id,
            'region_id')

        logger.info(f'Fetching devices within region: {region_id}')

        device_ids = await self.__device_repository.get_devices_ids_by_region(
            region_id=region_id)

        if not any(device_ids):
            logger.info(f'No devices defined for region: {region_id}')
            raise NoDevicesDefinedForRegionException(
                region_id=region_id)

        logger.info(f'Building cache keys for device IDs')
        keys = [CacheKey.device_key(
            device_id=device_id
        ) for device_id in device_ids]

        logger.info(f'Purging {len(keys)} cached devices')
        await self.__cache_client.__client.delete(*keys)

        return {
            'keys': keys
        }

    # TODO: Move to separate service w/ above
    async def clear_cache(
        self
    ):
        logger.info(f'Clearing all distributed service cache')

        keys = await self.__cache_client.__client.keys('*')
        logger.info(f'Keys to purge: {len(keys or [])}')

        if not any(keys):
            return list()

        await self.__cache_client.__client.delete(*keys)

        return keys
