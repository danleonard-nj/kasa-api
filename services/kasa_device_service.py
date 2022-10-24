from typing import Tuple

from clients.kasa_client import KasaClient
from data.repositories.kasa_device_repository import KasaDeviceRepository
from domain.cache import CacheExpiration, CacheKey
from domain.kasa.device import KasaDevice
from domain.kasa.preset import KasaPreset
from domain.rest import KasaRequest, KasaResponse, UpdateDeviceRequest
from framework.clients.cache_client import CacheClientAsync
from framework.logger.providers import get_logger
from framework.serialization.utilities import serialize
from utils.concurrency import DeferredTasks

from services.kasa_history_service import KasaHistoryService
from services.kasa_preset_service import KasaPresetSevice
from services.kasa_region_service import KasaRegionService

logger = get_logger(__name__)


def where(items, func):
    results = []
    for item in items:
        if func(item) is True:
            results.append(item)
    return results


class KasaDeviceService:
    def __init__(self, container=None):
        self.__kasa_client: KasaClient = container.resolve(
            KasaClient)
        self.__device_repository: KasaDeviceRepository = container.resolve(
            KasaDeviceRepository)
        self.__preset_service: KasaPresetSevice = container.resolve(
            KasaPresetSevice)
        self.__history_service: KasaHistoryService = container.resolve(
            KasaHistoryService)
        self.__region_service: KasaRegionService = container.resolve(
            KasaRegionService
        )
        self.__cache_client: CacheClientAsync = container.resolve(
            CacheClientAsync)

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
            logger.info(f'No cached value, fetching device from database')
            device = await self.__device_repository.get({
                'device_id': device_id
            })

            await self.__cache_client.set_json(
                key=CacheKey.device_key(
                    device_id=device_id),
                value=device,
                ttl=CacheExpiration.days(7))

        if device is None:
            raise Exception(f'No device with the ID {device_id} exists')

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
        devices = await self.__cache_client.get_json(
            key=CacheKey.device_list())

        if devices is None:
            logger.info(f'No cached value, fetching devices')
            devices = await self.__device_repository.get_all()

            await self.__cache_client.set_json(
                key=CacheKey.device_list(),
                ttl=CacheExpiration.days(7),
                value=devices)

        kasa_devices = [
            KasaDevice(device)
            for device in devices
        ]

        return kasa_devices

    async def sync_devices(self):
        logger.info('Syncing devices')

        # Clear existing stored devices
        setup_tasks = DeferredTasks()
        setup_tasks.add_task(
            self.expire_cached_device_list())

        # Delete all devices
        setup_tasks.add_task(
            self.__device_repository.collection.delete_many(
                filter={}))

        _, delete_results = await setup_tasks.run()

        logger.info(f'Deleted device count: {delete_results.acknowledged}')
        logger.info('Fetching devices from client')

        devices = await self.__kasa_client.get_devices()

        logger.info(
            f'Client device response: {serialize(devices)}')

        inserts = DeferredTasks()
        device_results = []

        for device in devices.device_list:
            logger.info(f'Syncing device: {serialize(device)}')
            kasa_device = KasaDevice.from_kasa_device_params(
                data=device)

            logger.info(f'Successfully parsed device {kasa_device.device_id}')

            entity = kasa_device.to_dict()
            device_results.append(entity)

            logger.info(f'Inserting device: {kasa_device.device_id}')
            inserts.add_task(
                self.__device_repository.insert(
                    document=entity))

        await inserts.run()

        logger.info('Device sync completed successfully')
        return device_results

    async def set_device_state(
        self,
        device: KasaDevice,
        preset: KasaPreset
    ) -> Tuple[KasaRequest, KasaResponse]:
        '''
        Set a device state to a given preset
        '''

        logger.info(
            f'Set device state: {device.device_id}: Preset: {preset.preset_id}')

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
            kasa_request=kasa_request)

        logger.info(f'Client results: {client_results}')
        if isinstance(client_results, list):
            response = [
                res.to_dict()
                for res in client_results]
        else:
            response = client_results.to_dict()

        return (kasa_request, response)

    async def update_device(
        self,
        update_request: UpdateDeviceRequest
    ):
        logger.info(f'Update device: {update_request.to_dict()}')

        bust_cache = DeferredTasks(
            self.expire_cached_device(
                device_id=update_request.device_id),
            self.expire_cached_device_list())

        await bust_cache.run()

        if update_request.device_id is None or update_request.device_id == '':
            raise Exception('Invalid device ID')

        device = await self.get_device(
            device_id=update_request.device_id)

        device.device_name = update_request.device_name
        device.device_type = update_request.device_type
        device.region_id = update_request.region_id

        logger.info(f'Updated device: {device.to_dict()}')

        await self.__device_repository.update({
            'device_id': update_request.device_id
        }, device.to_dict())

        return device

    async def set_device_region(
        self,
        device_id: str,
        region_id: str
    ):
        # Expire cached device and device list
        expirations = DeferredTasks(
            self.expire_cached_device(
                device_id=device_id),
            self.expire_cached_device_list())
        await expirations.run()

        logger.info(f'Set device region: {device_id}: {region_id}')

        if region_id is None or region_id == '':
            raise Exception('Must provide a region')

        fetch = DeferredTasks(
            self.__region_service.get_region(
                region_id=region_id),
            self.__device_repository.get({
                'device_id': device_id
            }))

        region, entity = await fetch.run()

        logger.info(f'Device: {entity}')
        if entity is None:
            raise Exception(f"No device with the ID '{device_id}' exists")

        device = KasaDevice(
            data=entity)

        logger.info(f'Region: {region.to_dict()}')
        device.region_id = region_id

        logger.info(
            f'Updating device: {device.device_name} to region: {region.region_name}')

        await self.__device_repository.replace({
            'device_id': device_id
        }, device.to_dict())

        return device

    async def get_devices_by_region(
        self
    ):
        logger.info('Fetching devices and regions')

        fetch = DeferredTasks(
            self.__region_service.get_regions(),
            self.get_all_devices())

        regions, devices = await fetch.run()

        results = []
        for region in regions:
            region_devices = where(
                devices, lambda x: x.region_id == region.region_id)

            results.append(region.to_dict() | {
                'devices': region_devices
            })

        return results
