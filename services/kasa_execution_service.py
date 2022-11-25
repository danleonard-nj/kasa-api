from typing import Dict, List, Tuple

from framework.clients.cache_client import CacheClientAsync
from framework.concurrency import TaskCollection
from framework.logger.providers import get_logger

from clients.identity_client import IdentityClient
from clients.kasa_client import KasaClient
from domain.cache import CacheExpiration, CacheKey
from domain.exceptions import NullArgumentException
from domain.kasa.device import KasaDevice
from domain.kasa.preset import KasaPreset
from domain.kasa.scene import KasaScene
from domain.rest import MappedSceneRequest
from services.kasa_device_service import KasaDeviceService
from services.kasa_preset_service import KasaPresetSevice
from utils.helpers import apply, get_map

logger = get_logger(__name__)


class KasaExecutionService:
    def __init__(
        self,
        device_service: KasaDeviceService,
        preset_service: KasaPresetSevice,
        identity_client: IdentityClient,
        cache_client: CacheClientAsync,
        kasa_client: KasaClient
    ):
        NullArgumentException.if_none(device_service, 'device_service')
        NullArgumentException.if_none(preset_service, 'preset_service')
        NullArgumentException.if_none(identity_client, 'identity_client')
        NullArgumentException.if_none(cache_client, 'cache_client')
        NullArgumentException.if_none(kasa_client, 'kasa_client')

        self.__device_service = device_service
        self.__preset_service = preset_service
        self.__identity_client = identity_client
        self.__cache_client = cache_client
        self.__kasa_client = kasa_client

    async def get_token(
        self
    ) -> str:
        '''
        Get a Azure AD token to pass to outbound events
        to allow the event handler to call back to the
        Kasa service
        '''

        logger.info(f'Fetching token from cache')
        token = await self.__cache_client.get_cache(
            key=CacheKey.event_token())

        if token is None:
            logger.info(f'No cached token, fetching from client')
            token = await self.__identity_client.get_token(
                client_name='kasa-api')

            await self.__cache_client.set_cache(
                key=CacheKey.event_token(),
                value=token,
                ttl=CacheExpiration.minutes(45))

        return token

    async def get_device_state_tasks(
        self,
        preset_map: Dict[str, KasaPreset],
        device_map: Dict[str, KasaDevice],
        preset_scene_maps: List[MappedSceneRequest],
        region_id: str = None
    ) -> TaskCollection:
        '''
        Get a deferred task collection comprised of all the
        Kasa client set device state requests
        '''

        NullArgumentException.if_none(preset_map, 'preset_map')
        NullArgumentException.if_none(device_map, 'device_map')
        NullArgumentException.if_none(preset_scene_maps, 'preset_scene_maps')

        tasks = TaskCollection()
        # device_states = list()

        for scene_map in preset_scene_maps:
            logger.info(
                f'Handling preset map: {scene_map.device_id}: {scene_map.preset_id}')

            device = device_map.get(scene_map.device_id)
            preset = preset_map.get(scene_map.preset_id)

            if region_id is not None and region_id != '':
                logger.info(
                    f'Filtering scene execution by region: {region_id}')

                # Skip setting device state if device is not in
                # the provided region
                if device.region_id != region_id:
                    logger.info(
                        f'Skipping device not in provided region: {device}')
                    continue

            logger.info(f'Queueing device state request')
            tasks.add_task(
                self.__device_service.set_device_state(
                    device=device,
                    preset=preset))

        return tasks

    async def get_device_preset_maps(
        self
    ) -> Tuple[Dict[str, KasaDevice], Dict[str, KasaPreset]]:
        '''
        Get device and preset maps
        '''

        # Fetch full list of devices and presets
        storage_tasks = TaskCollection(
            self.__device_service.get_all_devices(),
            self.__preset_service.get_all_presets())

        devices, presets = await storage_tasks.run()

        logger.info('Building device and preset maps')
        device_map = get_map(devices, 'device_id', False)
        preset_map = get_map(presets, 'preset_id', False)

        return device_map, preset_map

    async def execute_scene(
        self,
        scene: KasaScene,
        region_id: str = None,
    ) -> List[MappedSceneRequest]:
        '''
        Execute a scene by sending mapped device presets to
        the Kasa client and dispatch events to store the last
        known state of the device
        '''

        NullArgumentException.if_none(scene, 'scene')

        # Refresh the token if necessary so when the events are processed
        # there is a working token available
        logger.info(f'Refresh cached Kasa token')
        await self.__kasa_client.refresh_token()

        preset_scene_maps = scene.get_device_preset_pairs()

        # Get lookup maps for all Kasa device and preset entities
        # as the ID and entity as key value pairs respectively
        device_map, preset_map = await self.get_device_preset_maps()
        set_device_state_tasks = TaskCollection()

        # Get the collection of tasks to set each device state
        # from the Kasa client and a collection of the new device
        # preset values
        set_device_state_tasks = await self.get_device_state_tasks(
            preset_map=preset_map,
            device_map=device_map,
            preset_scene_maps=preset_scene_maps,
            region_id=region_id)

        # Run tasks to set device state and fetch a
        # token to pass to the device state history events
        kasa = await set_device_state_tasks.run()

        return {
            'map': apply(preset_scene_maps, lambda x: x.to_dict()),
            'results': kasa
        }
