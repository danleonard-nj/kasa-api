from typing import List

from framework.concurrency import TaskCollection
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger

from clients.kasa_client import KasaClient
from domain.features import FeatureKey
from domain.kasa.client_response import KasaClientResponse
from domain.kasa.scene import KasaScene
from domain.rest import MappedSceneRequest
from services.kasa_client_response_service import KasaClientResponseService
from services.kasa_device_service import KasaDeviceService
from services.kasa_preset_service import KasaPresetSevice
from framework.clients.feature_client import FeatureClientAsync
from utils.helpers import get_map

logger = get_logger(__name__)


class KasaExecutionService:
    def __init__(
        self,
        device_service: KasaDeviceService,
        preset_service: KasaPresetSevice,
        feature_client: FeatureClientAsync,
        client_response_service: KasaClientResponseService,
        kasa_client: KasaClient
    ):
        ArgumentNullException.if_none(device_service, 'device_service')
        ArgumentNullException.if_none(preset_service, 'preset_service')
        ArgumentNullException.if_none(kasa_client, 'kasa_client')

        ArgumentNullException.if_none(
            feature_client, 'feature_client')
        ArgumentNullException.if_none(
            client_response_service, 'client_response_service')

        self.__device_service = device_service
        self.__preset_service = preset_service
        self.__client_response_service = client_response_service
        self.__feature_client = feature_client
        self.__kasa_client = kasa_client

    async def __get_client_responses(
        self,
        device_ids: List[str]
    ) -> KasaClientResponse:

        get_responses = TaskCollection(*[
            self.__client_response_service.get_client_response(
                device_id=device_id
            ) for device_id in device_ids])

        return await get_responses.run()

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

        ArgumentNullException.if_none(scene, 'scene')

        ignore_client_responses = await self.__feature_client.is_enabled(
            feature_key=FeatureKey.KasaIgnoreClientResponsePreset)

        # Refresh the token if necessary so when the events are processed
        # there is a working token available
        logger.info(f'Refresh cached Kasa token')
        await self.__kasa_client.refresh_token()

        scene_mapping = scene.get_scene_mapping()

        get_devices_presets = TaskCollection(
            self.__device_service.get_devices(
                device_ids=scene_mapping.device_ids,
                region_id=region_id),
            self.__preset_service.get_presets(
                preset_ids=scene_mapping.preset_ids),
            self.__get_client_responses(
                device_ids=scene_mapping.device_ids
            ))

        devices, presets, client_responses = await get_devices_presets.run()

        devices_map = get_map(
            items=devices,
            key='device_id',
            is_dict=False)

        presets_map = get_map(
            items=presets,
            key='preset_id',
            is_dict=False)

        response_map = get_map(
            items=client_responses,
            key='device_id',
            is_dict=False)

        set_device_state = TaskCollection()
        for mapping in scene_mapping.mapping:
            device = devices_map.get(mapping.device_id)
            preset = presets_map.get(mapping.preset_id)

            # Verify the mappings are valid but do not throw for missing
            # devices/presets to allow the rest of the scene to run
            if device is None:
                logger.info(
                    f'Device {mapping.device_id} in scene {scene.scene_id} is not known')
                continue

            if preset is None:
                logger.info(
                    f'Preset {mapping.preset_id} in scene {scene.scene_id} is not known')
                continue

            # TODO: Need to periodically sync device current states to handle outside changed
            # Get the last known client response for a given device and only
            # update if the requested preset is different
            response = response_map.get(mapping.device_id)

            # TODO: Verify the preset was actually set/acknowleded (i.e. last response success)
            if (ignore_client_responses
                    or response is None
                    or response.preset_id != preset.preset_id):

                logger.info(
                    f'{mapping.device_id}: {mapping.preset_id}: Setting device state')

                set_device_state.add_task(
                    self.__device_service.set_device_state(
                        device=device,
                        preset=preset))
            else:
                # TODO: Rules for certain devices to always send a device state request?
                # Particularly devices prone to being turned on/off manually - if the device
                # was in an off state.
                logger.info(
                    f'{mapping.device_id}: {mapping.preset_id}: Device is already set to requested preset')

        # Run tasks to set device state and fetch a
        # token to pass to the device state history events
        kasa = await set_device_state.run()

        return {
            'results': kasa
        }
