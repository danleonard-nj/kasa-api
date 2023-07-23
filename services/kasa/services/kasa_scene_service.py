from typing import List, Union

from framework.logger.providers import get_logger

from data.repositories.kasa_scene_repository import KasaSceneRepository
from domain.exceptions import (NullArgumentException, SceneExistsException,
                               SceneNotFoundException)
from domain.kasa.scene import KasaScene
from domain.rest import (CreateSceneRequest, MappedSceneRequest,
                         RunSceneRequest, UpdateSceneRequest)
from services.kasa_execution_service import KasaExecutionService
from utils.helpers import DateTimeUtil

logger = get_logger(__name__)


class KasaSceneService:
    def __init__(
        self,
        scene_repository: KasaSceneRepository,
        execution_service: KasaExecutionService
    ):
        self.__scene_repository = scene_repository
        self.__execution_service = execution_service

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

        kasa_scene = KasaScene.from_dict(
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

        logger.info(f'Fetching scene from db: {update_request.scene_id}')

        # Verify the scene exists
        entity = await self.__scene_repository.get({
            'scene_id': update_request.scene_id
        })

        # Scene not found
        if entity is None:
            raise SceneNotFoundException(
                scene_id=update_request.scene_id)

        existing_scene = KasaScene.from_dict(
            data=entity)

        # Merge the existing scene with the update request
        # TODO: Move some/all of this logic to domain object
        data = (
            existing_scene.to_dict() |
            update_request.to_dict() | {
                'modified_date': DateTimeUtil.timestamp()
            }
        )

        updated_scene = KasaScene.from_dict(data=data)

        logger.info(f'Updating scene: {existing_scene.scene_id}')

        # Replace the scene document in the db
        update_result = await self.__scene_repository.replace(
            selector=updated_scene.get_selector(),
            document=updated_scene.to_dict())

        logger.info(f'Updated count: {update_result.modified_count}')

        return updated_scene

    async def get_all_scenes(
        self,
    ) -> List[KasaScene]:
        '''
        Get the list of scenes
        '''

        logger.info('Get all scenes')

        entities = await self.__scene_repository.get_all()

        kasa_scenes = [
            KasaScene.from_dict(data=entity)
            for entity in entities
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

        scenes = [KasaScene.from_dict(data=entity)
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
