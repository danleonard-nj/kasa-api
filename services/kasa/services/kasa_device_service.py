from typing import Dict, List, Tuple

from deprecated import deprecated
from framework.clients.cache_client import CacheClientAsync
from framework.concurrency import TaskCollection
from framework.logger.providers import get_logger
from framework.exceptions.nulls import ArgumentNullException
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
from domain.rest import DeviceSyncResponse, KasaRequest, KasaResponse, UpdateDeviceRequest
from services.kasa_client_response_service import KasaClientResponseService
from services.kasa_preset_service import KasaPresetSevice
from services.kasa_region_service import KasaRegionService

logger = get_logger(__name__)


class KasaDeviceService:
    def __init__(
        self,
        kasa_client: KasaClient,
        device_repository: KasaDeviceRepository,
        region_service: KasaRegionService,
        preset_service: KasaPresetSevice,
        cache_client: CacheClientAsync,
        client_response_service: KasaClientResponseService
    ):
        self.__kasa_client = kasa_client
        self.__device_repository = device_repository
        self.__region_service = region_service
        self.__cache_client = cache_client
        self.__client_response_service = client_response_service
        self.__preset_service = preset_service

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

    async def sync_devices(
        self,
        destructive: bool = False
    ):
        logger.info('Syncing devices')

        # Fetch all known devices from database
        device_entities = await self.__device_repository.get_all()
        known_devices = [
            KasaDevice(data=device)
            for device in device_entities
        ]

        logger.info(f'Known devices fetched: {len(known_devices)}')

        # Create a lookup by device IDs
        known_device_lookups = {
            device.device_id: device
            for device in known_devices
        }

        # Get all Kasa device from Kasa
        # service
        kasa_devices = await self.__kasa_client.get_devices()
        kasa_device_list = [
            KasaDevice.from_kasa_device_json_object(
                kasa_device=kasa_device)
            for kasa_device in kasa_devices.device_list
        ]

        logger.info(f'Kasa devices fetched: {len(kasa_device_list)}')

        # Create a lookup by device IDs
        kasa_device_lookups = {
            kasa_device.device_id: kasa_device
            for kasa_device in kasa_device_list
        }

        known_ids = list(known_device_lookups.keys())
        kasa_ids = list(kasa_device_lookups.keys())

        # Devices w/ a database record but
        # are unknown to Kasa client
        unknown_devices = list(set(known_ids) - set(kasa_ids))

        # Devices known to Kasa client but
        # missing a database record
        missing_devices = list(set(kasa_ids) - set(known_ids))

        logger.info(f'Unknown devices: {unknown_devices}')
        logger.info(f'Missing devices: {missing_devices}')

        created = list()
        for device_id in missing_devices:
            logger.info(f'Syncing missing device: {device_id}')
            device = kasa_device_lookups.get(device_id)

            created.append(device)

            await self.__device_repository.insert(
                document=device.to_dict())
            logger.info(f'Synced device: {device.to_dict()}')

        if not destructive:
            logger.info(f'{len(created)} devices created')
            return DeviceSyncResponse(
                destructive=destructive,
                created=created)

        logger.info(f'Removing unknown Kasa devices')

        removed = list()
        for device_id in unknown_devices:
            logger.info(f'Removing device: {device_id}')
            device = known_device_lookups.get(device_id)

            removed.append(device)

            await self.__device_repository.delete(
                selector=device.get_selector())

        return DeviceSyncResponse(
            destructive=destructive,
            created=created,
            removed=removed)

    async def get_device_state(
        self,
        device_id: str
    ):
        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')

        return await self.__kasa_client.get_device_state(
            device_id=device_id)

    async def set_device_state(
        self,
        device: KasaDevice,
        preset: KasaPreset,
        kasa_token: str = None
    ) -> Tuple[KasaRequest, KasaResponse]:
        '''
        Set a device state to a given preset
        '''

        ArgumentNullException.if_none(device, 'device')
        ArgumentNullException.if_none(preset, 'preset')

        logger.info(
            f'Set device state: {device.device_id}: Preset: {preset.preset_id}')

        if not none_or_whitespace(kasa_token):
            logger.info(f'Using provided client token: {kasa_token}')

        # Fetch the Kasa client request from cache if we have it
        # kasa_request = await self.__cache_client.get_json(
        #     key=CacheKey.kasa_request(
        #         preset_id=preset.preset_id,
        #         device_id=device.device_id))

        # if kasa_request is None:
        typed_device = preset.to_device_preset(
            device=device)

        kasa_request = preset.to_request(
            device=typed_device).get_request_body()

        logger.info(f'Sending Kasa device state request')

        state_key = typed_device.state_key()
        logger.info(f'Device state key: {device.device_name}: {state_key}')

        # Run Kasa client commands
        client_results = await self.__kasa_client.set_device_state(
            kasa_request=kasa_request,
            kasa_token=kasa_token,
            device_id=device.device_id,
            preset_id=preset.preset_id,
            state_key=state_key)

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
        await self.__cache_client.client.delete(*keys)

        return {
            'keys': keys
        }

    # TODO: Move to separate service w/ above
    async def clear_cache(
        self
    ):
        logger.info(f'Clearing all distributed service cache')

        keys = await self.__cache_client.client.keys('*')
        logger.info(f'Keys to purge: {len(keys or [])}')

        await self.__cache_client.client.delete(*keys)
        return keys

    async def get_auto_sync_enabled_devices(
        self
    ):
        logger.info(f'Get devices with automated sync enabled')

        entities = await self.__device_repository.get_automated_sync_devices()

        models = [KasaDevice(data=entity)
                  for entity in entities]

        return models

    async def __create_kasa_device(
        self,
        client_device: Dict
    ) -> None:

        kasa_device = KasaDevice.from_kasa_device_json_object(
            kasa_device=client_device)

        await self.__device_repository.insert(
            document=kasa_device.to_dict())
