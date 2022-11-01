import asyncio
from typing import List

from data.repositories.kasa_scene_category_repository import \
    KasaSceneCategoryRepository
from data.repositories.kasa_scene_repository import KasaSceneRepository
from domain.cache import CacheExpiration, CacheKey
from domain.kasa.scene import KasaScene, KasaSceneCategory
from domain.rest import (CreateSceneCategoryRequest, CreateSceneRequest,
                         MappedSceneRequest, RunSceneRequest,
                         UpdateSceneRequest)
from framework.clients.cache_client import CacheClientAsync
from framework.concurrency import TaskCollection
from framework.logger.providers import get_logger
from framework.validators.nulls import none_or_whitespace

from services.kasa_execution_service import KasaExecutionService

logger = get_logger(__name__)


class KasaSceneService:
    def __init__(
        self,
        scene_repository: KasaSceneRepository,
        scene_category_repository: KasaSceneCategoryRepository,
        cache_client: CacheClientAsync,
        execution_service: KasaExecutionService
    ):
        self.__scene_repository = scene_repository
        self.__scene_category_repository = scene_category_repository
        self.__cache_client = cache_client
        self.__execution_service = execution_service

    async def expire_cached_scene(
        self,
        scene_id: str
    ) -> None:
        '''
        Expire the scene from cache
        '''

        logger.info(f'Expire cached scene: {scene_id}')

        await self.__cache_client.delete_key(
            key=CacheKey.scene_key(
                scene_id=scene_id))

    async def expire_cached_scene_list(
        self
    ) -> None:
        '''
        Expire the scene list from cache
        '''

        logger.info(f'Expire cached scene list')

        await self.__cache_client.delete_key(
            key=CacheKey.scene_list())

    async def create_scene(
        self,
        request: CreateSceneRequest
    ) -> KasaScene:
        '''
        Create a scene
        '''

        logger.info('Create scene')
        await self.expire_cached_scene_list()

        scene_exists = await self.__scene_repository.scene_exists(
            scene_name=request.scene_name)

        if scene_exists:
            raise Exception(
                f'Scene with the name {request.scene_name} already exists')

        kasa_scene = KasaScene.create_scene(
            data=request.to_dict())

        logger.info('Inserting scene')
        inserted_scene = await self.__scene_repository.insert(
            document=kasa_scene.to_dict())

        logger.info(f'Caching created scene: {kasa_scene.scene_id}')
        await self.__cache_client.set_json(
            value=kasa_scene.to_dict(),
            ttl=CacheExpiration.days(7),
            key=CacheKey.scene_key(
                scene_id=kasa_scene.scene_id))

        logger.info(f'Inserted document: {str(inserted_scene.inserted_id)}')
        return kasa_scene

    async def get_scene(
        self,
        scene_id: str
    ) -> KasaScene:
        '''
        Get a scene
        '''

        logger.info(f'Get scene: {scene_id}')

        # Attempt to fetch the scene from cache
        scene = await self.__cache_client.get_json(
            key=CacheKey.scene_key(
                scene_id=scene_id))

        if scene is None:
            logger.info(f'No cached value, fetching scene')
            scene = await self.__scene_repository.get({
                'scene_id': scene_id
            })

            await self.__cache_client.set_json(
                key=CacheKey.scene_key(
                    scene_id=scene_id),
                value=scene,
                ttl=CacheExpiration.days(7))

        if scene is None:
            raise Exception(f'No scene with the ID {scene_id} exists')

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

        logger.info(f'Delete scene: {scene_id}')

        await asyncio.gather(
            self.expire_cached_scene_list(),
            self.expire_cached_scene(
                scene_id=scene_id))

        scene = await self.__scene_repository.get({
            'scene_id': scene_id
        })

        if scene is None:
            raise Exception(f'No scene with the ID {scene_id} exists')

        scene = await self.__scene_repository.delete({
            'scene_id': scene_id
        })

        return {'result': True}

    async def update_scene(
        self,
        scene: UpdateSceneRequest
    ) -> KasaScene:
        '''
        Update a scene
        '''

        logger.info(
            f'Scene: {scene.scene_id}: Updating Kasa scene: {scene.scene_id}')

        await asyncio.gather(
            self.expire_cached_scene_list(),
            self.expire_cached_scene(
                scene_id=scene.scene_id))

        kasa_scene = KasaScene(
            data=scene.to_dict())

        logger.info(
            f'Updating scene: {kasa_scene.scene_id}')

        updated_scene = await self.__scene_repository.update(
            selector={'scene_id': kasa_scene.scene_id},
            values=kasa_scene.to_dict())
        logger.info(
            f'Updated count: {updated_scene.modified_count}')

        return kasa_scene

    async def get_scenes_by_category(
        self,
        category_id: str
    ):
        logger.info(f'Get scenes by category: {category_id}')

        if none_or_whitespace(category_id):
            raise Exception('Scene category ID cannot be null')

        entities = await self.__scene_repository.query({
            'scene_category_id': category_id
        })

        scenes = [
            KasaScene(data=entity)
            for entity in entities
        ]

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

    async def run_scene(
        self,
        request: RunSceneRequest
    ) -> List[MappedSceneRequest]:
        '''
        Run a scene
        '''

        scene = await self.get_scene(
            scene_id=request.scene_id)

        return await self.__execution_service.execute_scene(
            scene=scene,
            region_id=request.region_id)

    async def create_scene_category(
        self,
        request: CreateSceneCategoryRequest
    ) -> KasaSceneCategory:
        logger.info(f'Create scene category: {request.scene_category}')

        if request.scene_category is None or request.scene_category == '':
            raise Exception(f'Scene category name is required')

        category = await self.__scene_category_repository.get({
            'scene_category': request.scene_category
        })

        if category is not None:
            raise Exception(
                f"A scene category with the name '{request.scene_category}' exists")

        scene_category = KasaSceneCategory.create_category(
            category_name=request.scene_category)

        entity = scene_category.to_dict()
        logger.info(f'Scene category: {entity}')

        await self.__scene_category_repository.insert(
            entity)

        return scene_category

    async def get_scene_categories(
        self,
    ) -> List[KasaSceneCategory]:
        logger.info(f'Get scene categories')

        entities = await self.__scene_category_repository.get_all()

        categories = [
            KasaSceneCategory(data=entity)
            for entity in entities
        ]

        return categories

    async def delete_scene_category(
        self,
        scene_category_id: str,
    ) -> List[KasaSceneCategory]:
        logger.info(f'Get scene categories')

        if none_or_whitespace(scene_category_id):
            raise Exception('Scene category ID is required')

        category_entity = await self.__scene_category_repository.get({
            'scene_category_id': scene_category_id
        })

        if category_entity is None:
            raise Exception(
                f"No scene category with the ID '{scene_category_id}' exists")

        logger.info('Removing scenes from deleted category')

        category = KasaSceneCategory(
            data=category_entity)

        # Fetch all scenes tied to the scene category
        scene_entities = await self.__scene_repository.query(
            filter=category.get_selector())

        logger.info(f'Scenes in category: {len(scene_entities)}')

        if any(scene_entities):
            update_scenes = TaskCollection()

            for scene_entity in scene_entities:
                scene = KasaScene(data=scene_entity)

                # Remove the scene from the category
                logger.info(f'Removing scene from category: {scene.scene_id}')
                scene.scene_category_id = None

                update_scenes.add_task(
                    self.__scene_repository.replace(
                        selector=scene.get_selector(),
                        document=scene.to_dict()))

            await update_scenes.run()

        result = await self.__scene_category_repository.delete({
            'scene_category_id': scene_category_id
        })

        return {
            'deleted': result.deleted_count
        }
