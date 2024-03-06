from framework.mongo.mongo_repository import MongoRepositoryAsync
from motor.motor_asyncio import AsyncIOMotorClient

from data.constants import MongoConstants


class KasaSceneCategoryRepository(MongoRepositoryAsync):
    def __init__(
        self,
        client: AsyncIOMotorClient
    ):
        super().__init__(
            client=client,
            database=MongoConstants.DatabaseName,
            collection=MongoConstants.KasaSceneCategoryCollectionName)

    async def get_category_by_name(
        self,
        category_name: str
    ) -> dict:
        '''
        Get a scene category by name
        '''

        return await self.get({
            'scene_category': category_name
        })
