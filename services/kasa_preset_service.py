from typing import List

from data.repositories.kasa_preset_repository import KasaPresetRepository
from domain.cache import CacheExpiration, CacheKey
from domain.kasa.preset import KasaPreset
from domain.rest import (CreatePresetRequest, DeleteResponse,
                         UpdatePresetRequest)
from framework.clients.cache_client import CacheClientAsync
from framework.logger.providers import get_logger
from framework.validators.nulls import not_none
from utils.concurrency import DeferredTasks

logger = get_logger(__name__)


class KasaPresetSevice:
    def __init__(self, container=None):
        self.__preset_repository: KasaPresetRepository = container.resolve(
            KasaPresetRepository)
        self.__cache_client: CacheClientAsync = container.resolve(
            CacheClientAsync)

    async def expire_cached_preset(
        self,
        preset_id: str
    ) -> None:
        '''
        Expire a cached preset
        '''

        logger.info(f'Expire cache key: {preset_id}')
        await self.__cache_client.delete_key(f'preset-{preset_id}*')

    async def expire_cached_preset_list(
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

        await self.expire_cached_preset_list()

        kasa_preset = KasaPreset(
            data=request.body).with_id()

        logger.info(f'Preset name: {kasa_preset.preset_name}')
        exists = await self.__preset_repository.preset_exists_by_name(
            preset_name=kasa_preset.preset_name)

        if exists:
            raise Exception(
                f'Preset with the name {kasa_preset.preset_name} already exists')

        document = await self.__preset_repository.insert(
            document=kasa_preset.to_json())

        await self.__cache_client.set_json(
            key=CacheKey.preset_key(
                kasa_preset.preset_id),
            value=document,
            ttl=24 * 60 * 7)

        logger.info(f'Inserted record: {str(document.inserted_id)}')
        return kasa_preset

    async def update_preset(
        self,
        request: UpdatePresetRequest
    ) -> KasaPreset:
        '''
        Update a preset
        '''
        # Verify the preset exists
        exists = await self.__preset_repository.preset_exists_by_id(
            preset_id=request.preset_id)

        logger.info(f'Preset exists: {exists}')
        if not exists:
            raise Exception(
                f'No preset with the ID {request.preset_id} exists')

        # Expire the cached preset and the cached
        # preset list
        expiration_tasks = DeferredTasks(
            self.expire_cached_preset_list(),
            self.expire_cached_preset(preset_id=request.preset_id))

        await expiration_tasks.run()

        kasa_preset = KasaPreset(
            data=request.body)

        # Update the preset
        logger.info(f'Preset name: {kasa_preset.preset_name}')
        update_result = await self.__preset_repository.update(
            selector={'preset_id': kasa_preset.preset_id},
            values=kasa_preset.to_json())

        logger.info(f'Modified count: {update_result.modified_count}')
        return kasa_preset

    async def get_preset(
        self,
        preset_id: str
    ) -> KasaPreset:
        '''
        Get a preset
        '''

        preset = await self.__cache_client.get_json(
            key=CacheKey.preset_key(
                preset_id=preset_id
            ))

        # No cached preset, fetch and cache
        if preset is None:
            logger.info(f'No cached value, fetching preset')
            preset = await self.__preset_repository.get({
                'preset_id': preset_id
            })

            await self.__cache_client.set_json(
                ttl=CacheExpiration.days(7),
                key=CacheKey.preset_key(
                    preset_id=preset_id),
                value=preset)

        if not preset:
            raise Exception(f'No preset with the ID {preset_id} exists')

        kasa_preset = KasaPreset(
            data=preset)

        return kasa_preset

    async def delete_preset(
        self,
        preset_id: str
    ) -> DeleteResponse:
        '''
        Delete a preset
        '''

        not_none(preset_id, 'preset_id')

        # Verify preset exists
        preset = await self.__preset_repository.get({
            'preset_id': preset_id
        })

        if not preset:
            raise Exception(f'No preset with the ID {preset_id} exists')

        # Expire cached preset if exists
        expiration_tasks = DeferredTasks(
            self.expire_cached_preset(preset_id=preset_id),
            self.expire_cached_preset_list())

        await expiration_tasks.run()

        kasa_preset = KasaPreset(
            data=preset)

        logger.info(f'Deleting preset: {kasa_preset.preset_id}')
        delete_result = await self.__preset_repository.delete({
            'preset_id': kasa_preset.preset_id
        })

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
            logger.info(f'No cached value, fetching preset list')
            presets = await self.__preset_repository.get_all()

            await self.__cache_client.set_json(
                key=CacheKey.preset_list(),
                ttl=CacheExpiration.days(7),
                value=presets)

        # Create preset models from stored presets
        kasa_presets = [
            KasaPreset(data=preset)
            for preset in presets
        ]

        return kasa_presets
