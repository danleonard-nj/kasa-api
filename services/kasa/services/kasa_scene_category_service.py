import uuid
from typing import List

from data.repositories.kasa_scene_category_repository import \
    KasaSceneCategoryRepository
from domain.exceptions import (NullArgumentException,
                               SceneCategoryExistsException,
                               SceneCategoryNotFoundException)
from domain.kasa.scene import KasaSceneCategory
from domain.rest import CreateSceneCategoryRequest
from framework.concurrency import TaskCollection
from framework.exceptions.nulls import ArgumentNullException
from framework.logger import get_logger
from services.kasa_scene_service import KasaSceneService
from utils.helpers import DateTimeUtil

logger = get_logger(__name__)


class KasaSceneCategoryService:
    def __init__(
        self,
        scene_category_repository: KasaSceneCategoryRepository,
        scene_service: KasaSceneService,
    ):
        self._scene_category_repository = scene_category_repository
        self._scene_service = scene_service

    async def create_scene_category(
        self,
        request: CreateSceneCategoryRequest
    ) -> KasaSceneCategory:

        ArgumentNullException.if_none(
            request, 'request')
        ArgumentNullException.if_none_or_whitespace(
            request.scene_category, 'scene_category')

        logger.info(f'Create scene category: {request.scene_category}')

        category = await self._scene_category_repository.get_category_by_name(
            category_name=request.scene_category)

        # Throw if the scene doesn't exist
        if category is not None:
            raise SceneCategoryExistsException(
                f"A scene category with the name '{request.scene_category}' exists")

        scene_category = KasaSceneCategory(
            scene_category_id=str(uuid.uuid4()),
            scene_category=request.scene_category,
            created_date=DateTimeUtil.timestamp()
        )

        entity = scene_category.to_dict()
        logger.info(f'Scene category: {entity}')

        await self._scene_category_repository.insert(
            entity)

        return scene_category

    async def get_scene_categories(
        self,
    ) -> List[KasaSceneCategory]:
        logger.info(f'Get scene categories')

        entities = await self._scene_category_repository.get_all()

        categories = [KasaSceneCategory.from_entity(entity)
                      for entity in entities]

        return categories

    async def delete_scene_category(
        self,
        scene_category_id: str,
    ) -> List[KasaSceneCategory]:

        NullArgumentException.if_none_or_whitespace(
            scene_category_id, 'scene_category_id')

        logger.info(f'Get scene categories')

        # Fetch the scene cageory
        category_entity = await self._scene_category_repository.get({
            'scene_category_id': scene_category_id
        })

        if category_entity is None:
            raise SceneCategoryNotFoundException(
                scene_category_id=scene_category_id)

        logger.info('Removing scenes from deleted category')

        # Fetch all scenes tied to the scene category
        scenes = await self._scene_service.get_scenes_by_category(
            scene_category_id=scene_category_id)

        logger.info(f'Scenes in category: {len(scenes)}')

        if not any(scenes):
            logger.info(f'No scenes to clear from category')
            return

        update_scenes = TaskCollection()

        for scene in scenes:
            # Remove the scene from the category
            logger.info(f'Removing scene from category: {scene.scene_id}')
            scene.scene_category_id = None

            update_scenes.add_task(
                self.__scene_repository.replace(
                    selector=scene.get_selector(),
                    document=scene.to_dict()))

        await update_scenes.run()

        result = await self._scene_category_repository.delete({
            'scene_category_id': scene_category_id
        })

        return {
            'deleted': result.deleted_count
        }
