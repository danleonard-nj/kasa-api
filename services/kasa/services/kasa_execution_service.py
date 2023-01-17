import asyncio
from typing import List, Union

from framework.clients.feature_client import FeatureClientAsync
from framework.concurrency import TaskCollection
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger

from clients.kasa_client import KasaClient
from domain.features import FeatureKey
from domain.kasa.device import KasaDevice
from domain.kasa.preset import KasaPreset
from domain.kasa.scene import KasaPresetDeviceMapping, KasaScene
from domain.rest import SetDeviceStateRequest
from services.kasa_client_response_service import KasaClientResponseService
from services.kasa_device_service import KasaDeviceService
from services.kasa_device_state_service import KasaDeviceStateService
from services.kasa_event_service import KasaEventService
from services.kasa_preset_service import KasaPresetSevice
from framework.validators.nulls import none_or_whitespace

logger = get_logger(__name__)


class KasaExecutionService:
    def __init__(
        self,
        device_service: KasaDeviceService,
        preset_service: KasaPresetSevice,
        feature_client: FeatureClientAsync,
        client_response_service: KasaClientResponseService,
        kasa_device_state_service: KasaDeviceStateService,
        event_service: KasaEventService,
        kasa_client: KasaClient
    ):
        ArgumentNullException.if_none(device_service, 'device_service')
        ArgumentNullException.if_none(preset_service, 'preset_se                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              rvice')
        ArgumentNullException.if_none(kasa_client, 'kasa_client')

        ArgumentNullException.if_none(
            feature_client, 'feature_client')
        ArgumentNullException.if_none(
            client_response_service, 'client_response_service')

        self.__device_service = device_service
        self.__feature_client = feature_client
        self.__device_state_service = kasa_device_state_service
        self.__event_service = event_service
        self.__preset_service = preset_service

    async def __is_device_update_eligible(
        self,
        device: KasaDevice,
        preset: KasaPreset
    ) -> bool:
        # Fetch the stored device state if flag is enabled
        logger.info(f'Fetching state for device: {device.device_id}')
        device_state = await self.__device_state_service.get_device_state(
            device_id=device.device_id)

        logger.info(f'Device state: {device_state.to_dict()}')

        # Get the target state key (state of the device set
        # to the target preset)
        device_preset = preset.to_device_preset(
            device=device)

        # Target device preset state key
        current_key = device_state.state_key
        target_key = device_preset.state_key()

        logger.info(f'{device.device_name}: {current_key} -> {target_key}')

        return device_state.state_key != target_key,

    async def set_device_state(
        self,
        preset: KasaPreset,
        device_id: str,
        region_id: str = None
    ) -> Union[SetDeviceStateRequest, None]:

        logger.info(f'Setting state for device: {device_id}')

        device = await self.__device_service.get_device(
            device_id=device_id)

        use_stored_device_state = await self.__feature_client.is_enabled(
            feature_key=FeatureKey.KasaIgnoreClientResponsePreset)

        # If state compare flag is enabled, compare the current
        # (stored) device state with the target state and don't
        # send the update request if no change occurs
        if use_stored_device_state:
            logger.info(f'{device.device_name}: Comparing device state')

            update_eligible = await self.__is_device_update_eligible(
                device=device,
                preset=preset)

            logger.info(
                f'Device: {device.device_name}: Eligible: {update_eligible}')

            # Short out if device isn't eligible for update
            if not update_eligible:
                logger.info(f'Device: {device.device_name}: Skipping update')
                return

        # Skip the update if this device is not in the region
        # if a region is provided
        if (region_id is not None
                and region_id != device.device_id):

            logger.info(f'Device excluded by region: {device_id}')
            return

        logger.info(f'Set preset: {device.to_dict()}: {preset.preset_name}')

        # Send the device update request to the Kasa client
        await self.__device_service.set_device_state(
            preset=preset,
            device=device)

        typed_device = preset.to_device_preset(
            device=device)

        state_key = typed_device.state_key()

        # state_key = device.state_key()
        logger.info(f'Device key: {device_id}: {state_key}')

        # Return the updated device state key
        return SetDeviceStateRequest.create_request(device_id=device_id,
                                                    preset_id=preset.preset_id,
                                                    state_key=state_key)

    async def execute_scene(
        self,
        scene: KasaScene,
        region_id: str = None
    ):
        logger.info(f'Run scene: {scene.scene_name}')
        scene_mapping = scene.get_mapping()

        logger.info(f'Fetching scene presets')
        presets = await self.__get_presets(
            mappings=scene_mapping)

        lookups = {
            preset.preset_id: preset
            for preset in presets
        }

        set_devices = TaskCollection()

        for mapping in scene_mapping:
            for device_id in mapping.devices:

                # Only send state change requests to
                # devices in requested regions, if a
                # reion was provie
                if none_or_whitespace(region_id):

                    preset = lookups.get(mapping.preset_id)
                    set_devices.add_task(self.set_device_state(
                        device_id=device_id,
                        preset=preset,
                        region_id=region_id))

        update_state_results = await set_devices.run()

        logger.info('Firing device state update dispatch events')
        asyncio.create_task(self.__dispatch_update_device_state_events(
            update_state_results=update_state_results
        ))

        return update_state_results

    async def __get_presets(
        self,
        mappings: List[KasaPresetDeviceMapping]
    ):
        get_presets = TaskCollection(*[
            self.__preset_service.get_preset(
                preset_id=mapping.preset_id)
            for mapping in mappings
        ])

        return await get_presets.run()

    async def __dispatch_update_device_state_events(
        self,
        update_state_results: List[Union[SetDeviceStateRequest, None]]
    ):
        # Filter any nulls (cases where device was not
        # eligible for an update)
        update_requests = [request for request
                           in update_state_results
                           if request is not None]

        logger.info(f'Sending {len(update_requests)} update event requests')
