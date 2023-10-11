import asyncio
from typing import List

from framework.clients.cache_client import CacheClientAsync
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger

from data.repositories.kasa_preset_repository import KasaPresetRepository
from domain.cache import CacheExpiration, CacheKey
from domain.exceptions import PresetExistsException, PresetNotFoundException
from domain.kasa.preset import KasaPreset
from domain.rest import (CreatePresetRequest, DeleteResponse,
                         UpdatePresetRequest)

logger = get_logger(__name__)


class KasaPresetSevice:
    def __init__(
        self,
        preset_repository: KasaPresetRepository,
        cache_client: CacheClientAsync
    ):
        ArgumentNullException.if_none(preset_repository, 'preset_repository')
        ArgumentNullException.if_none(cache_client, 'cache_client')

        self.__preset_repository = preset_repository
        self.__cache_client = cache_client

    async def create_preset(
        self,
        request: CreatePresetRequest
    ) -> KasaPreset:
        '''
        Create a preset
        '''

        ArgumentNullException.if_none(request, 'request')

        # Create new preset model with new preset ID
        kasa_preset = KasaPreset.create_preset(
            data=request.body)

        logger.info(f'Preset name: {kasa_preset.preset_name}')

        # Verify the preset name doesn't already exist
        exists = await self.__preset_repository.preset_exists_by_name(
            preset_name=kasa_preset.preset_name)

        # If a preset already exists w/ the same name
        if exists:
            logger.info(f'Preset already exists: {kasa_preset.preset_name}')
            raise PresetExistsException(
                preset_name=kasa_preset.preset_name)

        # Insert preset
        result = await self.__preset_repository.insert(
            document=kasa_preset.to_dict())

        cache_key = CacheKey.preset_list()
        logger.info(f'Preset list cache key: {cache_key}')

        # Delete the cached preset and preset list if it exists
        asyncio.create_task(
            self.__cache_client.delete_key(cache_key))
        asyncio.create_task(
            self.__cache_client.delete_key(CacheKey.preset_list()))

        logger.info(f'Preset document: {str(result.inserted_id)}')

        return kasa_preset

    async def update_preset(
        self,
        update_request: UpdatePresetRequest
    ) -> KasaPreset:
        '''
        Update a preset
        '''

        ArgumentNullException.if_none(update_request, 'request')
        ArgumentNullException.if_none(update_request.body, 'body')
        ArgumentNullException.if_none_or_whitespace(
            update_request.preset_id, 'preset_id')

        entity = await self.__preset_repository.get_preset_by_id(
            preset_id=update_request.preset_id)

        if entity is None:
            logger.info(f'Preset not found: {update_request.preset_id}')
            raise PresetNotFoundException(
                preset_id=update_request.preset_id)

        # Parse preset model from update request
        kasa_preset = KasaPreset.from_dict(
            data=update_request.body)

        # Update the mutable fields of the preset
        kasa_preset.update_preset(
            preset_name=update_request.preset_name,
            device_type=update_request.device_type,
            definition=update_request.definition)

        logger.info(f'Preset name: {kasa_preset.preset_name}')

        update_result = await self.__preset_repository.update(
            selector=kasa_preset.get_selector(),
            values=kasa_preset.to_dict())

        cache_key = CacheKey.preset_key(preset_id=kasa_preset.preset_id)
        logger.info(f'Preset cache key: {cache_key}')

        # Delete the cached preset if it exists and the preset list
        asyncio.create_task(
            self.__cache_client.delete_key(cache_key))
        asyncio.create_task(
            self.__cache_client.delete_key(CacheKey.preset_list()))

        logger.info(f'Modified count: {update_result.modified_count}')

        return kasa_preset

    async def get_preset(
        self,
        preset_id: str
    ) -> KasaPreset:
        '''
        Get a preset
        '''

        ArgumentNullException.if_none_or_whitespace(preset_id, 'preset_id')

        cache_key = CacheKey.preset_key(
            preset_id=preset_id)

        logger.info(f'Get preset: {preset_id}: {cache_key}')

        preset = await self.__cache_client.get_json(
            key=cache_key)

        if preset is not None:
            logger.info(f'Preset found in cache: {preset_id}')
            return KasaPreset.from_dict(
                data=preset)

        logger.info(f'Fetching preset from database: {preset_id}')
        entity = await self.__preset_repository.get_preset_by_id(
            preset_id=preset_id)

        # Preset doesn't exist
        if entity is None:
            logger.info(f'Preset not found: {preset_id}')
            raise PresetNotFoundException(
                preset_id=preset_id)

        # Cache the preset asynchonously
        asyncio.create_task(
            self.__cache_client.set_json(
                key=cache_key,
                value=entity,
                ttl=CacheExpiration.hours(24)))

        # Create preset model from document
        kasa_preset = KasaPreset.from_dict(
            data=entity)

        return kasa_preset

    async def delete_preset(
        self,
        preset_id: str
    ) -> DeleteResponse:
        '''
        Delete a preset
        '''

        ArgumentNullException.if_none_or_whitespace(preset_id, 'preset_id')

        # Verify preset exists
        preset = await self.__preset_repository.get_preset_by_id(
            preset_id=preset_id
        )

        if preset is None:
            logger.info(f'Preset not found: {preset_id}')
            raise PresetNotFoundException(
                preset_id=preset_id)

        # Parse preset model from document
        kasa_preset = KasaPreset.from_dict(
            data=preset)

        logger.info(f'Deleting preset: {kasa_preset.preset_id}')

        delete_result = await self.__preset_repository.delete_preset_by_id(
            preset_id=kasa_preset.preset_id
        )

        cache_key = CacheKey.preset_list()
        logger.info(f'Preset list cache key: {cache_key}')

        # Delete the cached device list if it exists
        asyncio.create_task(
            self.__cache_client.delete_key(cache_key))
        asyncio.create_task(
            self.__cache_client.delete_key(CacheKey.preset_list()))

        return DeleteResponse(
            delete_result=delete_result)

    async def get_all_presets(
        self
    ):
        '''
        Get all presets
        '''

        logger.info('Get all presets')

        preset_entities = await self.__cache_client.get_json(
            key=CacheKey.preset_list())

        if preset_entities is None:
            logger.info('Fetching presets from database')
            preset_entities = await self.__preset_repository.get_all()

        # Cache the preset list asynchonously
        asyncio.create_task(
            self.__cache_client.set_json(
                key=CacheKey.preset_list(),
                value=preset_entities,
                ttl=CacheExpiration.hours(24)))

        presets = [KasaPreset.from_dict(data=entity)
                   for entity in preset_entities]

        return presets

    async def get_presets_by_ids(
        self,
        preset_ids: List[str]
    ) -> List[KasaPreset]:

        ArgumentNullException.if_none(preset_ids, 'preset_ids')

        logger.info(f'Get presets: {preset_ids}')

        preset_entities = await self.__cache_client.get_json(
            key=CacheKey.preset_list())

        if preset_entities is None:
            logger.info(f'Fetching presets from database: {preset_ids}')
            preset_entities = await self.__preset_repository.get_presets(
                preset_ids=preset_ids)

        # Cache the preset list asynchonously
        asyncio.create_task(
            self.__cache_client.set_json(
                key=CacheKey.preset_list(),
                value=preset_entities,
                ttl=CacheExpiration.hours(24)))

        presets = [KasaPreset.from_dict(data=entity)
                   for entity in preset_entities]

        return presets
