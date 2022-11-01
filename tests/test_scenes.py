import pytest
from data.repositories.kasa_scene_repository import KasaSceneRepository
from unittest.mock import Mock
from utils.helpers import (
    TestData,
    get_mock_async_result,
)
from utils.provider import ContainerProvider
from app import app

from framework.testing.base_api import ApiTest
from framework.testing.helpers import (
    inject_test_dependency,
    guid
)


@pytest.mark.asyncio
class SceneTests(ApiTest):
    def setUp(self) -> None:
        self.configure(
            app=app,
            provider=ContainerProvider)

        self.mock_scene_repository = Mock()

        inject_test_dependency(
            provider=ContainerProvider,
            _type=KasaSceneRepository,
            instance=self.mock_scene_repository)

    @pytest.mark.asyncio
    async def test_get_scenes(self):
        builder = TestData()
        mock_scenes = [builder.get_scene() for _ in range(10)]

        self.mock_scene_repository.get_all.return_value = mock_scenes

        result = await self.send_request(
            method='GET',
            endpoint='/api/scene')

        self.assertEqual(200, result.status_code)
        self.assertIsNotNone(result.json)

    async def test_get_scene(self):
        builder = TestData()
        mock_scene = builder.get_scene()

        self.mock_scene_repository.get.return_value = get_mock_async_result(
            value=mock_scene)
        self.mock_cache_client.get_cache.return_value = get_mock_async_result(
            value=None)

        result = await self.send_request(
            method='GET',
            endpoint=f'/api/scene/{guid()}')

        self.assertEqual(200, result.status_code)
        self.assertIsNotNone(result.json)
