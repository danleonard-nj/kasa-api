from datetime import datetime
from typing import List

from framework.clients.cache_client import CacheClientAsync
from framework.concurrency import TaskCollection
from framework.logger.providers import get_logger

from data.repositories.kasa_preset_repository import KasaPresetRepository
from domain.cache import CacheExpiration, CacheKey
from domain.exceptions import (NullArgumentException, PresetExistsException,
                               PresetNotFoundException)
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
        NullArgumentException.if_none(preset_repository, 'preset_repository')
        NullArgumentException.if_none(cache_client, 'cache_client')

        self.__preset_repository = preset_repository
        self.__cache_client = cache_client

    async def expire_cached_preset(
        self,
        preset_id: str
    ) -> None:
        '''
        Expire a cached preset
        '''

        NullArgumentException.if_none_or_whitespace(
            preset_id, 'preset_id')

        logger.info(f'Expire cache key: {preset_id}')
        await self.__cache_client.delete_key(f'preset-{preset_id}*')

    async def __expire_cached_preset_list(
        self
    ) -> None:
        '''
        Expire the cached preset list
        '''

        logger.info(f'Expiring preset list')
        await self.__cache_client.delete_key(
            CacheKey.preset_list())

    async def create_preset(
        self,
        request: CreatePresetRequest
    ) -> KasaPreset:
        '''
        Create a preset
        '''

        NullArgumentException.if_none(request, 'request')

        await self.__expire_cached_preset_list()

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

        await self.__cache_client.set_json(
            value=kasa_preset.to_dict(),
            ttl=CacheExpiration.days(7),
            key=CacheKey.preset_key(
                preset_id=kasa_preset.preset_id))

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

        logger.info(f'Modified count: {update_result.modified_count}')

        # Expire the cached preset and the cached
        # preset list
        expiration_tasks = TaskCollection(
            self.__expire_cached_preset_list(),
            self.expire_cached_preset(preset_id=update_request.preset_id))

        await expiration_tasks.run()

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

        entity = await self.__cache_client.get_json(
            key=CacheKey.preset_key(
                preset_id=preset_id
            ))

        if entity is not None:
            preset = KasaPreset(
                data=entity)

            logger.info(f'Returning cached preset: {preset.preset_id}')
            return preset

        entity = await self.__preset_repository.get({
            'preset_id': preset_id
        })

        if not entity:
            raise PresetNotFoundException(
                preset_id=preset_id)

        await self.__cache_client.set_json(
            ttl=CacheExpiration.days(7),
            value=entity,
            key=CacheKey.preset_key(
                preset_id=preset_id
            ))

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

        # Expire cached preset if exists
        expiration_tasks = TaskCollection(
            self.expire_cached_preset(preset_id=preset_id),
            self.__expire_cached_preset_list())
        await expiration_tasks.run()

        return DeleteResponse(
            delete_result=delete_result)

    async def get_all_presets(
        self
    ) -> List[KasaPreset]:
        '''
        Get all presets
        '''

        logger.info('Get all presets')

        presets = await self.__cache_client.get_json(
            key=CacheKey.preset_list())

        if presets is None:
            presets = await self.__preset_repository.get_all()

            await self.__cache_client.set_json(
                key=CacheKey.preset_list(),
                ttl=CacheExpiration.days(7),
                value=presets)

        # Create preset models from stored presets
        kasa_presets = [KasaPreset(data=preset)
                        for preset in presets]

        return kasa_presets

    async def get_presets(
        self,
        preset_ids: List[str]
    ):

        entities = await self.__preset_repository.get_presets(
            preset_ids=preset_ids)

        presets = [KasaPreset(data=entity)
                   for entity in entities]

        return presets
