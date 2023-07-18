import asyncio
from datetime import datetime
from typing import List

from framework.logger.providers import get_logger

from data.repositories.kasa_preset_repository import KasaPresetRepository
from domain.cache import CacheExpiration, CacheKey
from domain.exceptions import (NullArgumentException, PresetExistsException,
                               PresetNotFoundException)
from domain.kasa.preset import KasaPreset
from domain.rest import (CreatePresetRequest, DeleteResponse,
                         UpdatePresetRequest)
from framework.clients.cache_client import CacheClientAsync

logger = get_logger(__name__)


class KasaPresetSevice:
    def __init__(
        self,
        preset_repository: KasaPresetRepository,
        cache_client: CacheClientAsync
    ):
        NullArgumentException.if_none(preset_repository, 'preset_repository')
        NullArgumentException.if_none(cache_client, 'cache_client')

        self.__preset_repository = preset_repository
        self.__cache_client = cache_client

    async def create_preset(
        self,
        request: CreatePresetRequest
    ) -> KasaPreset:
        '''
        Create a preset
        '''

        NullArgumentException.if_none(request, 'request')

        # Create new preset model with new preset ID
        kasa_preset = KasaPreset.create_preset(
            data=request.body)
        kasa_preset.created_date = datetime.now()

        logger.info(f'Preset name: {kasa_preset.preset_name}')

        # Verify the preset name doesn't already exist
        exists = await self.__preset_repository.preset_exists_by_name(
            preset_name=kasa_preset.preset_name)

        if exists:
            raise PresetExistsException(
                preset_name=kasa_preset.preset_name)

        # Insert preset
        result = await self.__preset_repository.insert(
            document=kasa_preset.to_dict())

        cache_key = CacheKey.device_list()
        logger.info(f'Device list cache key: {cache_key}')

        asyncio.create_task(
            self.__cache_client.delete_key(cache_key))

        logger.info(f'Inserted record: {str(result.inserted_id)}')
        return kasa_preset

    async def update_preset(
        self,
        update_request: UpdatePresetRequest
    ) -> KasaPreset:
        '''
        Update a preset
        '''

        NullArgumentException.if_none(
            update_request,
            'request')
        NullArgumentException.if_none(
            update_request.body,
            'body')
        NullArgumentException.if_none_or_whitespace(
            update_request.preset_id,
            'preset_id')

        entity = await self.__preset_repository.get({
            'preset_id': update_request.preset_id
        })

        if entity is None:
            raise PresetNotFoundException(
                preset_id=update_request.preset_id)

        kasa_preset = KasaPreset(
            data=update_request.body)

        kasa_preset.update_preset(
            preset_name=update_request.preset_name,
            device_type=update_request.device_type,
            definition=update_request.definition)

        # Update the preset
        logger.info(f'Preset name: {kasa_preset.preset_name}')

        update_result = await self.__preset_repository.update(
            selector=kasa_preset.get_selector(),
            values=kasa_preset.to_dict())

        cache_key = CacheKey.preset_key(
            preset_id=kasa_preset.preset_id)
        logger.info(f'Preset cache key: {cache_key}')

        # Delete the cached preset if it exists
        asyncio.create_task(
            self.__cache_client.delete_key(cache_key))

        logger.info(f'Modified count: {update_result.modified_count}')

        return kasa_preset

    async def get_preset(
        self,
        preset_id: str
    ) -> KasaPreset:
        '''
        Get a preset
        '''

        NullArgumentException.if_none_or_whitespace(
            preset_id, 'preset_id')

        cache_key = CacheKey.preset_key(
            preset_id=preset_id)

        logger.info(f'Get preset: {preset_id}: {cache_key}')

        preset = await self.__cache_client.get_json(
            key=cache_key)

        if preset is not None:
            return KasaPreset(
                data=preset)

        entity = await self.__preset_repository.get({
            'preset_id': preset_id
        })

        if entity is None:
            raise PresetNotFoundException(
                preset_id=preset_id)

        # Cache the preset asynchonously
        asyncio.create_task(
            self.__cache_client.set_json(
                key=cache_key,
                value=entity,
                ttl=CacheExpiration.hours(24)))

        kasa_preset = KasaPreset(
            data=entity)

        return kasa_preset

    async def delete_preset(
        self,
        preset_id: str
    ) -> DeleteResponse:
        '''
        Delete a preset
        '''

        NullArgumentException.if_none_or_whitespace(
            preset_id, 'preset_id')

        # Verify preset exists
        preset = await self.__preset_repository.get({
            'preset_id': preset_id
        })

        if preset is None:
            raise PresetNotFoundException(
                preset_id=preset_id)

        kasa_preset = KasaPreset(
            data=preset)

        logger.info(f'Deleting preset: {kasa_preset.preset_id}')
        delete_result = await self.__preset_repository.delete({
            'preset_id': kasa_preset.preset_id
        })

        cache_key = CacheKey.preset_list()
        logger.info(f'Preset list cache key: {cache_key}')

        # Delete the cached device list if it exists
        asyncio.create_task(
            self.__cache_client.delete_key(cache_key))

        return DeleteResponse(
            delete_result=delete_result)

    async def get_all_presets(
        self
    ) -> List[KasaPreset]:
        '''
        Get all presets
        '''

        logger.info('Get all presets')

        presets = await self.__preset_repository.get_all()

        # Create preset models from stored presets
        kasa_presets = [KasaPreset(data=preset)
                        for preset in presets]

        return kasa_presets

    async def get_presets(
        self,
        preset_ids: List[str]
    ) -> List[KasaPreset]:

        entities = await self.__preset_repository.get_presets(
            preset_ids=preset_ids)

        presets = [KasaPreset(data=entity)
                   for entity in entities]

        return presets
