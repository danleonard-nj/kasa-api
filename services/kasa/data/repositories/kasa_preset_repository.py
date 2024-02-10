from typing import Dict, List, Union

from framework.mongo.mongo_repository import MongoRepositoryAsync
from motor.motor_asyncio import AsyncIOMotorClient

from data.constants import MongoConstants


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
        preset_ids: List[str]
    ) -> list[dict]:

        query = {
            'preset_id': {
                '$in': preset_ids
            }
        }

        results = self.collection.find(query)

        return await results.to_list(
            length=None)

    async def get_preset_by_id(
        self,
        preset_id: str
    ) -> Union[dict, None]:

        query = {
            'preset_id': preset_id
        }

        return await self.collection.find_one(query)
