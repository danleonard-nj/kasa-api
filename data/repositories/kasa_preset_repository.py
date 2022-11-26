from data.constants import MongoConstants
from data.repositories.async_mongo_repository import MongoRepositoryAsync
from motor.motor_asyncio import AsyncIOMotorClient


class KasaPresetRepository(MongoRepositoryAsync):
    def __init__(
        self,
        client: AsyncIOMotorClient
    ):
        super().__init__(
            client=client,
            database=MongoConstants.DatabaseName,
            collection=MongoConstants.KasaPresetCollectionName)

    async def preset_exists_by_name(self, preset_name):
        value = await self.get({
            'preset_name': preset_name
        })
        return value is not None

    async def preset_exists_by_id(self, preset_id):
        value = await self.get({
            'preset_id': preset_id
        })
        return value is not None
