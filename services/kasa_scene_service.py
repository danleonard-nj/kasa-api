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
        await self.__expire_cached_scene_list()

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

        await self.__cache_client.set_json(
            value=kasa_scene.to_dict(),
            ttl=CacheExpiration.days(7),
            key=CacheKey.scene_key(
                scene_id=kasa_scene.scene_id))

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

        # Attempt to fetch the scene from cache
        scene = await self.__cache_client.get_json(
            key=CacheKey.scene_key(
                scene_id=scene_id
            ))

        if scene is None:
            logger.info(f'No cached value, fetching scene')
            scene = await self.__scene_repository.get({
                'scene_id': scene_id
            })

            await self.__cache_client.set_json(
                ttl=CacheExpiration.days(7),
                value=scene,
                key=CacheKey.scene_key(
                    scene_id=scene_id
                ))

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

        scenes = await self.__cache_client.get_json(
            key=CacheKey.scene_list())

        if scenes is None:
            logger.info(f'No cached value, fetching scene list')
            scenes = await self.__scene_repository.get_all()

            await self.__cache_client.set_json(
                key=CacheKey.scene_list(),
                ttl=CacheExpiration.days(7),
                value=scenes
            )

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

    # async def create_scene_category(
    #     self,
    #     request: CreateSceneCategoryRequest
    # ) -> KasaSceneCategory:

    #     NullArgumentException.if_none(
    #         request, 'request')

    #     logger.info(f'Create scene category: {request.scene_category}')

    #     if request.scene_category is None or request.scene_category == '':
    #         raise Exception(f'Scene category name is required')

    #     category = await self.__scene_category_repository.get({
    #         'scene_category': request.scene_category
    #     })

    #     if category is not None:
    #         raise Exception(
    #             f"A scene category with the name '{request.scene_category}' exists")

    #     scene_category = KasaSceneCategory.create_category(
    #         category_name=request.scene_category)

    #     entity = scene_category.to_dict()
    #     logger.info(f'Scene category: {entity}')

    #     await self.__scene_category_repository.insert(
    #         entity)

    #     return scene_category

    # async def get_scene_categories(
    #     self,
    # ) -> List[KasaSceneCategory]:
    #     logger.info(f'Get scene categories')

    #     entities = await self.__scene_category_repository.get_all()

    #     categories = [
    #         KasaSceneCategory(data=entity)
    #         for entity in entities
    #     ]

    #     return categories

    # async def delete_scene_category(
    #     self,
    #     scene_category_id: str,
    # ) -> List[KasaSceneCategory]:
    #     logger.info(f'Get scene categories')

    #     if none_or_whitespace(scene_category_id):
    #         raise Exception('Scene category ID is required')

    #     category_entity = await self.__scene_category_repository.get({
    #         'scene_category_id': scene_category_id
    #     })

    #     if category_entity is None:
    #         raise Exception(
    #             f"No scene category with the ID '{scene_category_id}' exists")

    #     logger.info('Removing scenes from deleted category')

    #     category = KasaSceneCategory(
    #         data=category_entity)

    #     # Fetch all scenes tied to the scene category
    #     scene_entities = await self.__scene_repository.query(
    #         filter=category.get_selector())

    #     logger.info(f'Scenes in category: {len(scene_entities)}')

    #     if any(scene_entities):
    #         update_scenes = TaskCollection()

    #         for scene_entity in scene_entities:
    #             scene = KasaScene(data=scene_entity)

    #             # Remove the scene from the category
    #             logger.info(f'Removing scene from category: {scene.scene_id}')
    #             scene.scene_category_id = None

    #             update_scenes.add_task(
    #                 self.__scene_repository.replace(
    #                     selector=scene.get_selector(),
    #                     document=scene.to_dict()))

    #         await update_scenes.run()

    #     result = await self.__scene_category_repository.delete({
    #         'scene_category_id': scene_category_id
    #     })

    #     return {
    #         'deleted': result.deleted_count
    #     }
