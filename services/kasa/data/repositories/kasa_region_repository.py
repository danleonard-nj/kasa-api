from framework.mongo.mongo_repository import MongoRepositoryAsync
from motor.motor_asyncio import AsyncIOMotorClient

from data.constants import MongoConstants


class KasaRegionRepository(MongoRepositoryAsync):
    def __init__(
        self,
        client: AsyncIOMotorClient
    ):
        super().__init__(
            client=client,
            database=MongoConstants.DatabaseName,
            collection=MongoConstants.KasaRegionCollectionName)
