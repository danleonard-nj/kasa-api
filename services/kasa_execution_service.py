from typing import List, Tuple

from clients.identity_client import IdentityClient
from clients.kasa_client import KasaClient
from clients.service_bus import QueueClient
from domain.cache import CacheExpiration, CacheKey
from domain.events import StoreDeviceStateEvent
from domain.kasa.device import KasaDevice
from domain.kasa.devices.state import DeviceState, StoredDeviceState
from domain.kasa.preset import KasaPreset
from domain.kasa.scene import KasaScene
from domain.rest import MappedSceneRequest
from framework.clients.cache_client import CacheClientAsync
from framework.configuration import Configuration
from framework.logger.providers import get_logger
from utils.concurrency import DeferredTasks
from utils.helpers import apply, get_map

from services.kasa_device_service import KasaDeviceService
from services.kasa_history_service import KasaHistoryService
from services.kasa_preset_service import KasaPresetSevice

logger = get_logger(__name__)


class KasaExecutionService:
    def __init__(
        self,
        container
    ):
        '''
        Construct an instance of scene execution service
        '''
        configuration = container.resolve(Configuration)
        self.__event_base_url = configuration.events.get('base_url')

        self.__device_service: KasaDeviceService = container.resolve(
            KasaDeviceService)
        self.__preset_service: KasaPresetSevice = container.resolve(
            KasaPresetSevice)
        self.__kasa_history_service: KasaHistoryService = container.resolve(
            KasaHistoryService)
        self.__identity_client: IdentityClient = container.resolve(
            IdentityClient)
        self.__cache_client: CacheClientAsync = container.resolve(
            CacheClientAsync)
        self.__kasa_client: KasaClient = container.resolve(
            KasaClient)
        self.__queue_client: QueueClient = container.resolve(
            QueueClient)

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

    async def dispatch_store_device_state_events(
        self,
        token: str,
        device_states: list[DeviceState]
    ) -> None:
        '''
        Dispatch events to capture and store the current
        device state for references to the last known state
        of the device
        '''

        events = list()
        for state in device_states:

            state = StoredDeviceState(
                device=state.device,
                preset=state.preset)

            event = StoreDeviceStateEvent(
                device_state=state,
                base_url=self.__event_base_url,
                auth_token=token)

            events.append(event)

        logger.info(f'Dispatching {len(events)} events')
        await self.__queue_client.send_messages(
            messages=[event.to_service_bus_message()
                      for event in events])

    async def get_device_state_tasks(
        self,
        preset_map: dict[str, KasaPreset],
        device_map: dict[str, KasaDevice],
        preset_scene_maps: list[MappedSceneRequest],
        region_id: str = None
    ) -> DeferredTasks:
        '''
           Get a deferred task collection comprised of all the
           Kasa client set device state requests
           '''

        deferred = DeferredTasks()
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
            deferred.add_task(
                self.__device_service.set_device_state(
                    device=device,
                    preset=preset))

            # TODO: Remove store device state features
            # logger.info(f'Storing device power state as: {preset.power_state}')
            # state = DeviceState.create_device_state(
            #     device=device,
            #     preset=preset)

            # device_states.append(state)

        return deferred

    async def get_device_preset_maps(
        self
    ) -> Tuple[dict[str, KasaDevice], dict[str, KasaPreset]]:
        '''
        Get device and preset maps
        '''

        # Fetch full list of devices and presets
        storage_tasks = DeferredTasks(
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

        # Refresh the token if necessary so when the events are processed
        # there is a working token available
        logger.info(f'Refresh cached Kasa token')
        await self.__kasa_client.refresh_token()

        preset_scene_maps = scene.get_device_preset_pairs()

        # Get lookup maps for all Kasa device and preset entities
        # as the ID and entity as key value pairs respectively
        device_map, preset_map = await self.get_device_preset_maps()
        set_device_state_tasks = DeferredTasks()

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

        # Dispatch store device state events
        # TODO: Remove store device state features
        # await self.dispatch_store_device_state_events(
        #     token=token,
        #     device_states=device_states)

        return {
            'map': apply(preset_scene_maps, lambda x: x.to_dict()),
            'results': kasa
        }
