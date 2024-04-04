from clients.kasa_client import KasaClient
from domain.kasa.preset import KasaPreset
from domain.kasa.scene import KasaPresetDeviceMapping, KasaScene
from domain.rest import SetDeviceStateRequest
from framework.concurrency import TaskCollection
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger
from framework.validators.nulls import none_or_whitespace
from services.kasa_device_service import KasaDeviceService
from services.kasa_preset_service import KasaPresetSevice

logger = get_logger(__name__)


class KasaExecutionService:
    def __init__(
        self,
        device_service: KasaDeviceService,
        preset_service: KasaPresetSevice,
        kasa_client: KasaClient,
    ):
        self._device_service = device_service
        self._preset_service = preset_service
        self._kasa_client = kasa_client

    async def execute_scene(
        self,
        scene: KasaScene,
        region_id: str = None
    ):

        ArgumentNullException.if_none(scene, 'scene')

        logger.info(f'Run scene: {scene.scene_name}')

        scene_mapping = scene.get_mapping()

        kasa_token, presets = await TaskCollection(
            self._kasa_client.get_kasa_token(),
            self._get_presets(mappings=scene_mapping)).run()

        # Lookup for preset by ID (minimize looping
        # in here)
        logger.info(f'Generating preset key lookup')
        lookups = {
            preset.preset_id: preset
            for preset in presets
            if preset is not None
        }

        tasks = TaskCollection()
        for mapping in scene_mapping:
            for device_id in mapping.devices:

                # Get the mapped preset for this device and set the state
                tasks.add_task(
                    self._try_set_device_state(
                        device_id=device_id,
                        preset=lookups.get(mapping.preset_id),
                        region_id=region_id,
                        kasa_token=kasa_token))

        set_results = await tasks.run()

        return [
            result for result in set_results
            if result is not None
        ]

    async def set_device_state(
        self,
        preset: KasaPreset,
        device_id: str,
        region_id: str = None,
        kasa_token: str = None,
    ) -> SetDeviceStateRequest | None:

        ArgumentNullException.if_none(preset, 'preset')
        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')

        logger.info(f'Setting state for device: {device_id}')

        device = await self._device_service.get_device(
            device_id=device_id)

        # Skip the update if this device is not in the region
        # if a region is provided
        if (not none_or_whitespace(region_id)
                and region_id != device.region_id):

            logger.info(f'Device excluded by region: {device_id}')
            return

        logger.info(
            f'Set device preset: {device.device_name}: {preset.preset_name}')

        # Send the device update request to the Kasa client
        await self._device_service.set_device_state(
            preset=preset,
            device=device,
            kasa_token=kasa_token)

        typed_device = preset.to_device_preset(
            device=device)

        state_key = typed_device.state_key()

        logger.info(
            f'{device.device_name}: Typed device state key: {state_key}')

        # Return the updated device state key
        return SetDeviceStateRequest.create_request(
            device_id=device_id,
            preset_id=preset.preset_id,
            state_key=state_key)

    async def _try_set_device_state(
        self,
        device_id: str,
        preset: KasaPreset,
        region_id: str,
        kasa_token: str = None
    ):
        '''
        Wrap device state updates so we don't
        fail the whole scene on a single bad
        call, log and swallow exception
        '''

        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')
        ArgumentNullException.if_none(preset, 'preset')

        try:
            return await self.set_device_state(
                device_id=device_id,
                preset=preset,
                region_id=region_id,
                kasa_token=kasa_token)
        except:
            logger.exception(
                f'Failed to set device: {device_id}: {preset.preset_name}')

    async def _get_presets(
        self,
        mappings: list[KasaPresetDeviceMapping]
    ) -> list[KasaPreset]:

        # Suppress these, we don't want to fail invoking
        # the scene entirely for a single missing preset
        async def wrap_get_preset(
            preset_id: str
        ):
            try:
                return await self._preset_service.get_preset(
                    preset_id=preset_id)
            except:
                return

        return await TaskCollection(*[
            wrap_get_preset(mapping.preset_id)
            for mapping in mappings
        ]).run()
