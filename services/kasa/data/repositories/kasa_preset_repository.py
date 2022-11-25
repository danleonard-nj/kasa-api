from typing import Dict, List
from data.constants import MongoConstants
from data.repositories.async_mongo_repository import MongoRepositoryAsync
from motor.motor_asyncio import AsyncIOMotorClient
from framework.validators.nulls import none_or_whitespace


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

    async def get_presets(
        self,
        preset_ids: List[str]
    ) -> List[Dict]:

        query = {
            'preset_id': {
                '$in': preset_ids
            }
        }

        results = self.collection.find(query)

        return await results.to_list(
            length=None)
