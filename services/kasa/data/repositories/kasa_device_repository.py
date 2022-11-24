from typing import Dict, List

from motor.motor_asyncio import AsyncIOMotorClient

from data.constants import MongoConstants
from data.repositories.async_mongo_repository import MongoRepositoryAsync
from domain.exceptions import NullArgumentException
from framework.validators.nulls import none_or_whitespace


class KasaDeviceRepository(MongoRepositoryAsync):
    def __init__(
        self,
        client: AsyncIOMotorClient
    ):
        super().__init__(
            client=client,
            database=MongoConstants.DatabaseName,
            collection=MongoConstants.KasaDeviceCollectionName)

    async def get_devices_by_region(
        self,
        region_id: str
    ) -> List[dict]:

        NullArgumentException.if_none_or_whitespace(region_id)

        results = self.collection.find({
            'device_region_id': region_id
        })

        return await results.to_list(
            length=None)

    async def get_devices(
        self,
        device_ids: List[str],
        region_id: str = None
    ) -> List[Dict]:

        query = {
            'device_id': {
                '$in': device_ids
            }
        }

        if not none_or_whitespace(region_id):
            query['region_id'] = region_id

        results = self.collection.find(
            query)

        return await results.to_list(
            length=None)
