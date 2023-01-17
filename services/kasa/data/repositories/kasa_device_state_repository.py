from motor.motor_asyncio import AsyncIOMotorClient

from data.constants import MongoConstants
from data.repositories.async_mongo_repository import MongoRepositoryAsync


class KasaDeviceStateRepository(MongoRepositoryAsync):
    def __init__(
        self,
        client: AsyncIOMotorClient
    ):
        super().__init__(
            client=client,
            database=MongoConstants.DatabaseName,
            collection=MongoConstants.KasaDeviceStateCategory)
