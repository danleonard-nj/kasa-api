from unittest.mock import AsyncMock

from data.repositories.kasa_scene_repository import KasaSceneRepository
from services.kasa_scene_service import KasaSceneService
from tests.buildup import ApplicationBase
from tests.helpers import TestHelper

helper = TestHelper()


def get_kasa_client(container):
    return AsyncMock()


class KasaSceneExecutionServiceTests(ApplicationBase):
    def setUp(self):
        self.repo: KasaSceneRepository = self.resolve(KasaSceneRepository)
        self.service: KasaSceneService = self.resolve(KasaSceneService)
