from data.constants import MongoConstants
from domain.queries import GetPresetsByPresetIdsQuery
from framework.mongo.mongo_repository import MongoRepositoryAsync
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

    async def delete_preset_by_id(
        self,
        preset_id: str
    ):
        return await self.collection.delete_one({
            'preset_id': preset_id
        })

    async def preset_exists_by_name(
        self,
        preset_name: str
    ):
        value = await self.get({
            'preset_name': preset_name
        })

        return value is not None

    async def preset_exists_by_id(
        self,
        preset_id: str
    ):
        value = await self.get({
            'preset_id': preset_id
        })

        return value is not None

    async def get_presets(
        self,
        preset_ids: list[str]
    ) -> list[dict]:

        query = GetPresetsByPresetIdsQuery(
            preset_ids=preset_ids)

        return await (self.collection
                      .find(query.get_query())
                      .to_list(length=None))

    async def get_preset_by_id(
        self,
        preset_id: str
    ) -> dict | None:

        return await self.collection.find_one({
            'preset_id': preset_id
        })
