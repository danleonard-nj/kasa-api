from data.repositories.kasa_scene_repository import KasaSceneRepository
from domain.cache import CacheExpiration, CacheKey
from domain.exceptions import SceneExistsException, SceneNotFoundException
from domain.kasa.scene import KasaScene
from domain.rest import (CreateSceneRequest, DeleteKasaSceneResponse,
                         MappedSceneRequest, RunSceneRequest,
                         UpdateSceneRequest)
from framework.clients.cache_client import CacheClientAsync
from framework.concurrency import TaskCollection
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger
from framework.validators.nulls import none_or_whitespace
from services.kasa_execution_service import KasaExecutionService
from utils.helpers import DateTimeUtil, fire_task

logger = get_logger(__name__)


class KasaDeviceServiceException(Exception):
    pass


class KasaSceneService:
    def __init__(
        self,
        scene_repository: KasaSceneRepository,
        execution_service: KasaExecutionService,
        cache_client: CacheClientAsync
    ):
        self._scene_repository = scene_repository
        self._execution_service = execution_service
        self._cache_client = cache_client

    async def create_scene(
        self,
        request: CreateSceneRequest
    ) -> KasaScene:
        '''
        Create a scene
        '''

        ArgumentNullException.if_none(request, 'request')

        logger.info('Create scene')

        # Verify the scene doesn't already exist
        scene_exists = await self._scene_repository.scene_exists(
            scene_name=request.scene_name)

        # Throw if it does
        if scene_exists:
            logger.info(f'Scene already exists: {request.scene_name}')
            raise SceneExistsException(
                scene_name=request.scene_name)

        # Create the scene model from the request
        kasa_scene = KasaScene.create_scene(
            data=request.to_dict())

        insert_result = await self._scene_repository.insert(
            document=kasa_scene.to_dict())

        logger.info(f'Insert result: {insert_result.inserted_id}')

        # Clear the cached scene list
        fire_task(self._cache_client.delete_key(
            key=CacheKey.scene_list()))

        return kasa_scene

    async def get_scene(
        self,
        scene_id: str
    ) -> KasaScene:
        '''
        Get a scene
        '''

        ArgumentNullException.if_none_or_whitespace(
            scene_id, 'scene_id')

        logger.info(f'Get scene: {scene_id}')

        key = CacheKey.scene_key(
            scene_id=scene_id)

        scene = await self._cache_client.get_json(
            key=key)

        if scene is not None:
            logger.info(f'Returning cached scene: {scene_id}')
            return KasaScene.from_dict(data=scene)

        logger.info(f'Fetching scene from db: {scene_id}')
        scene = await self._scene_repository.get_scene_by_id(
            scene_id=scene_id)

        # Throw if the scene is not found
        if scene is None:
            logger.info(f'Scene not found: {scene_id}')
            raise KasaDeviceServiceException(
                f"No scene with the ID '{scene_id}' exists")

        fire_task(self._cache_client.set_json(
            key=key,
            value=scene,
            ttl=CacheExpiration.hours(1)))

        return KasaScene.from_dict(
            data=scene)

    async def delete_scene(
        self,
        scene_id: str
    ) -> DeleteKasaSceneResponse:
        '''
        Delete a scene
        '''

        ArgumentNullException.if_none_or_whitespace(scene_id, 'scene_id')

        logger.info(f'Delete scene: {scene_id}')

        # Verify the scene actually exists
        scene = await self._scene_repository.get_scene_by_id(
            scene_id=scene_id
        )

        if scene is None:
            logger.info(f'Scene not found: {scene_id}')
            raise SceneNotFoundException(
                scene_id=scene_id)

        scene = KasaScene.from_dict(data=scene)

        # Delete the scene
        delete_result = await self._scene_repository.delete(
            scene.get_selector())

        # Clear the cahced scene and scene list
        fire_task(self._cache_client.delete(
            key=CacheKey.scene_key(scene_id)))
        fire_task(self._cache_client.delete(
            key=CacheKey.scene_list()))

        return DeleteKasaSceneResponse(
            modified_count=delete_result.deleted_count)

    async def update_scene(
        self,
        update_request: UpdateSceneRequest
    ) -> KasaScene:
        '''
        Update a scene
        '''

        ArgumentNullException.if_none(update_request, 'update_request')

        logger.info(f'Fetching scene from db: {update_request.scene_id}')

        if none_or_whitespace(update_request.scene_id):
            raise KasaDeviceServiceException('No valid scene ID provided')

        existing_scene = await self.get_scene(
            scene_id=update_request.scene_id)

        # Merge the existing scene with the update request
        # TODO: Move some/all of this logic to domain object
        data = (
            existing_scene.to_dict() |
            update_request.to_dict()
        )

        updated_scene = KasaScene.from_dict(data=data)
        updated_scene.modified_date = DateTimeUtil.timestamp()

        logger.info(f'Updating scene: {existing_scene.scene_id}')

        # Replace the scene document in the db
        update_result = await self._scene_repository.update(
            selector=updated_scene.get_selector(),
            values=updated_scene.to_dict())

        logger.info(f'Updated count: {update_result.modified_count}')

        await TaskCollection(
            self._cache_client.set_json(
                key=CacheKey.scene_key(update_request.scene_id),
                value=updated_scene.to_dict(),
                ttl=CacheExpiration.hours(24)),
            self._cache_client.delete_key(CacheKey.scene_list())
        ).run()

        return updated_scene

    async def get_all_scenes(
        self,
    ) -> list[KasaScene]:
        '''
        Get the list of scenes
        '''

        logger.info('Get all scenes')

        key = CacheKey.scene_list()

        entities = await self._cache_client.get_json(
            key=key)

        if entities is None:
            logger.info('No cached scenes found, fetching from db')
            entities = await self._scene_repository.get_all()

            fire_task(self._cache_client.set_json(
                key=key,
                value=entities,
                ttl=CacheExpiration.hours(24)))
        else:
            logger.info('Returning cached scenes')

        kasa_scenes = [KasaScene.from_dict(data=entity)
                       for entity in entities]

        return kasa_scenes

    async def get_scenes_by_category(
        self,
        scene_category_id: str
    ) -> list[KasaScene]:

        ArgumentNullException.if_none_or_whitespace(
            scene_category_id, 'scene_category_id')

        entities = await self._scene_repository.query({
            'scene_category_id': scene_category_id
        })

        if not any(entities):
            logger.info(f'No scenes found for category: {scene_category_id}')
            return list()

        scenes = [KasaScene.from_dict(data=entity)
                  for entity in entities]

        return scenes

    async def run_scene(
        self,
        request: RunSceneRequest
    ) -> list[MappedSceneRequest]:

        ArgumentNullException.if_none(request, 'request')
        ArgumentNullException.if_none_or_whitespace(
            request.scene_id, 'scene_id')

        logger.info(f'Running scene: {request.scene_id}')

        # Get the scene
        scene = await self.get_scene(
            scene_id=request.scene_id)

        # Execute the scene
        return await self._execution_service.execute_scene(
            scene=scene,
            region_id=request.region_id)
