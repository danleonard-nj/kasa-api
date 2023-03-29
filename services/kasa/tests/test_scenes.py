from data.repositories.kasa_scene_repository import KasaSceneRepository
from domain.kasa.scene import KasaScene
from domain.rest import CreateSceneRequest, UpdateSceneRequest
from services.kasa_scene_service import KasaSceneService
from tests.buildup import ApplicationBase
from tests.helpers import TestHelper

helper = TestHelper()


class KasaSceneServiceTests(ApplicationBase):
    async def asyncSetUp(
        self
    ) -> None:
        self.repo = self.resolve(KasaSceneRepository)
        self.service = self.resolve(KasaSceneService)

    async def insert_test_scene(self, **kwargs):
        repository: KasaSceneRepository = self.resolve(
            KasaSceneRepository)

        scene = helper.get_scene(**kwargs)
        await repository.insert(scene)

        return KasaScene(scene)

    async def test_create_scene(self):
        service: KasaSceneService = self.resolve(
            KasaSceneService)

        scene_name = self.guid()
        create_request = CreateSceneRequest({
            'scene_name': scene_name,
            'mapping': dict(),
            'flow': dict()
        })

        result = await service.create_scene(
            request=create_request)

        self.assertEqual(scene_name, result.scene_name)
        self.assertIsNotNone(result.scene_id)

    async def test_get_scene(self):
        # Arrange
        service: KasaSceneService = self.resolve(
            KasaSceneService)

        test_scene = await self.insert_test_scene()

        # Act
        scene = await service.get_scene(
            scene_id=test_scene.scene_id)

        # Assert
        self.assertIsNotNone(scene)
        self.assertEqual(test_scene.scene_id, scene.scene_id)
        self.assertEqual(test_scene.scene_category_id, scene.scene_category_id)
        self.assertEqual(test_scene.scene_name, scene.scene_name)

    async def test_update_scene(self):
        # Arrange
        service: KasaSceneService = self.resolve(KasaSceneService)
        test_scene = await self.insert_test_scene()

        updated_name = self.guid()
        updated_scene = test_scene.to_dict() | {
            'scene_name': updated_name
        }

        update_request = UpdateSceneRequest(
            data=updated_scene)

        existing_scene = await service.get_scene(
            scene_id=test_scene.scene_id)

        # Act
        result = await service.update_scene(
            update_request=update_request)

        # Assert
        self.assertEqual(updated_name, result.scene_name)
        self.assertEqual(test_scene.scene_id, result.scene_id)
        self.assertEqual(test_scene.scene_category_id,
                         result.scene_category_id)
        self.assertEqual(existing_scene.scene_name, test_scene.scene_name)

    async def test_get_scenes(
        self
    ):
        scenes = await self.service.get_all_scenes()

        self.assertTrue(len(scenes) > 0)
