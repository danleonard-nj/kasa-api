from data.repositories.kasa_scene_repository import KasaSceneRepository
from domain.exceptions import SceneExistsException, SceneNotFoundException
from domain.kasa.scene import KasaScene
from domain.rest import (CreateSceneRequest, DeleteKasaSceneResponse,
                         MappedSceneRequest, RunSceneRequest,
                         UpdateSceneRequest)
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger
from services.kasa_execution_service import KasaExecutionService
from utils.helpers import DateTimeUtil

logger = get_logger(__name__)


class KasaSceneService:
    def __init__(
        self,
        scene_repository: KasaSceneRepository,
        execution_service: KasaExecutionService
    ):
        self._scene_repository = scene_repository
        self._execution_service = execution_service

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

        scene = await self._scene_repository.get_scene_by_id(
            scene_id=scene_id
        )

        # Throw if the scene is not found
        if scene is None:
            logger.info(f'Scene not found: {scene_id}')
            raise SceneNotFoundException(
                scene_id=scene_id)

        kasa_scene = KasaScene.from_dict(
            data=scene)

        return kasa_scene

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

        # Verify the scene exists
        entity = await self._scene_repository.get_scene_by_id(
            scene_id=update_request.scene_id
        )

        # Scene not found
        if entity is None:
            logger.info(f'Scene not found: {update_request.scene_id}')
            raise SceneNotFoundException(
                scene_id=update_request.scene_id)

        existing_scene = KasaScene.from_dict(
            data=entity)

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

        return updated_scene

    async def get_all_scenes(
        self,
    ) -> list[KasaScene]:
        '''
        Get the list of scenes
        '''

        logger.info('Get all scenes')

        entities = await self._scene_repository.get_all()

        kasa_scenes = [
            KasaScene.from_dict(data=entity)
            for entity in entities
        ]

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
