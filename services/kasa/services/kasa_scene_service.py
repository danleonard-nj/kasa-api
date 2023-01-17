import asyncio
from typing import List, Union

from framework.clients.cache_client import CacheClientAsync
from framework.logger.providers import get_logger

from data.repositories.kasa_scene_repository import KasaSceneRepository
from domain.cache import CacheExpiration, CacheKey
from domain.exceptions import (NullArgumentException, SceneExistsException,
                               SceneNotFoundException)
from domain.kasa.scene import KasaScene
from domain.rest import (CreateSceneRequest, MappedSceneRequest,
                         RunSceneRequest, UpdateSceneRequest)
from services.kasa_execution_service import KasaExecutionService

logger = get_logger(__name__)


class KasaSceneService:
    def __init__(
        self,
        scene_repository: KasaSceneRepository,
        cache_client: CacheClientAsync,
        execution_service: KasaExecutionService
    ):
        self.__scene_repository = scene_repository
        self.__cache_client = cache_client
        self.__execution_service = execution_service

    async def __expire_cached_scene(
        self,
        scene_id: str
    ) -> None:
        '''
        Expire the scene from cache
        '''

        NullArgumentException.if_none_or_whitespace(
            scene_id, 'scene_id')

        logger.info(f'Expire cached scene: {scene_id}')

        await self.__cache_client.delete_key(
            key=CacheKey.scene_key(
                scene_id=scene_id
            ))

    async def __expire_cached_scene_list(
        self
    ) -> None:
        '''
        Expire the scene list from cache
        '''

        cache_key = CacheKey.scene_list()
        logger.info(f'Expire cached scene list')
        logger.info(f'Cache key: {cache_key}')

        await self.__cache_client.delete_key(
            key=cache_key)

    async def create_scene(
        self,
        request: CreateSceneRequest
    ) -> KasaScene:
        '''
        Create a scene
        '''

        NullArgumentException.if_none(request, 'request')

        logger.info('Create scene')

        # Verify the scene doesn't already exist
        scene_exists = await self.__scene_repository.scene_exists(
            scene_name=request.scene_name)

        # Throw if it does
        if scene_exists:
            raise SceneExistsException(
                scene_name=request.scene_name)

        kasa_scene = KasaScene.create_scene(
            data=request.to_dict())

        await self.__scene_repository.insert(
            document=kasa_scene.to_dict())

        return kasa_scene

    async def get_scene(
        self,
        scene_id: str
    ) -> KasaScene:
        '''
        Get a scene
        '''

        NullArgumentException.if_none_or_whitespace(
            scene_id, 'scene_id')

        logger.info(f'Get scene: {scene_id}')

        scene = await self.__scene_repository.get({
            'scene_id': scene_id
        })

        # Throw if the scene is not found
        if scene is None:
            raise SceneNotFoundException(
                scene_id=scene_id)

        kasa_scene = KasaScene(
            data=scene)

        return kasa_scene

    async def delete_scene(
        self,
        scene_id: str
    ) -> dict:
        '''
        Delete a scene
        '''

        NullArgumentException.if_none_or_whitespace(
            scene_id, 'scene_id')

        logger.info(f'Delete scene: {scene_id}')

        # Verify the scene actually exists
        scene = await self.__scene_repository.get({
            'scene_id': scene_id
        })

        if scene is None:
            raise SceneNotFoundException(
                scene_id=scene_id)

        # Delete the scene
        delete_result = await self.__scene_repository.delete({
            'scene_id': scene_id
        })

        # Expire the cached scene
        await asyncio.gather(
            self.__expire_cached_scene_list(),
            self.__expire_cached_scene(
                scene_id=scene_id))

        return {
            'result': delete_result.deleted_count
        }

    async def update_scene(
        self,
        update_request: UpdateSceneRequest
    ) -> KasaScene:
        '''
        Update a scene
        '''

        NullArgumentException.if_none(update_request, 'update_request')

        logger.info(
            f'Scene: {update_request.scene_id}: Updating Kasa scene: {update_request.scene_id}')

        # Verify the scene exists
        scene = await self.__scene_repository.get({
            'scene_id': update_request.scene_id
        })

        if scene is None:
            raise SceneNotFoundException(
                scene_id=update_request.scene_id)

        existing_scene = KasaScene(
            data=scene)

        updated_scene = KasaScene(
            data=existing_scene.to_dict() | update_request.to_dict())

        logger.info(
            f'Updating scene: {existing_scene.scene_id}')

        update_result = await self.__scene_repository.update(
            selector=updated_scene.get_selector(),
            values=updated_scene.to_dict())

        # Expire the cached scene and scene list
        await asyncio.gather(
            self.__expire_cached_scene_list(),
            self.__expire_cached_scene(
                scene_id=existing_scene.scene_id))

        logger.info(
            f'Updated count: {update_result.modified_count}')

        return updated_scene

    async def get_scenes_by_category(
        self,
        category_id: str
    ):
        NullArgumentException.if_none_or_whitespace(
            category_id, 'category_id')

        logger.info(f'Get scenes by category: {category_id}')

        entities = await self.__scene_repository.query({
            'scene_category_id': category_id
        })

        scenes = [KasaScene(data=entity)
                  for entity in entities]

        return scenes

    async def get_all_scenes(
        self,
    ) -> List[KasaScene]:
        '''
        Get the list of scenes
        '''

        logger.info('Get all scenes')

        scenes = await self.__scene_repository.get_all()

        kasa_scenes = [
            KasaScene(data=entity)
            for entity in scenes
        ]

        return kasa_scenes

    async def get_scenes_by_category(
        self,
        scene_category_id: str
    ) -> Union[List[KasaScene], None]:

        NullArgumentException.if_none_or_whitespace(
            scene_category_id, 'scene_category_id')

        entities = await self.__scene_repository.query({
            'scene_category_id': scene_category_id
        })

        if not any(entities):
            return

        scenes = [KasaScene(data=entity)
                  for entity in entities]

        return scenes

    async def run_scene(
        self,
        request: RunSceneRequest
    ) -> List[MappedSceneRequest]:
        '''
        Run a scene
        '''

        NullArgumentException.if_none(
            request, 'request')
        NullArgumentException.if_none_or_whitespace(
            request.scene_id, 'scene_id')

        scene = await self.get_scene(
            scene_id=request.scene_id)

        return await self.__execution_service.execute_scene(
            scene=scene,
            region_id=request.region_id)
