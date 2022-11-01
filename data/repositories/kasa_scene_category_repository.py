from data.constants import MongoConstants
from data.repositories.async_mongo_repository import MongoRepositoryAsync
from motor.motor_asyncio import AsyncIOMotorClient


class KasaSceneCategoryRepository(MongoRepositoryAsync):
    def __init__(
        self,
        client: AsyncIOMotorClient
    ):
        super().__init__(
            client=client,
            database=MongoConstants.DatabaseName,
            collection=MongoConstants.KasaSceneCategoryCollectionName)
