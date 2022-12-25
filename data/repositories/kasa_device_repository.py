from abc import abstractmethod
from typing import Dict, List

from framework.validators.nulls import none_or_whitespace
from motor.motor_asyncio import AsyncIOMotorClient

from data.constants import MongoConstants
from data.queries import GetDevicesByRegionQuery, GetDevicesQuery
from data.repositories.async_mongo_repository import MongoRepositoryAsync
from domain.exceptions import NullArgumentException
from framework.serialization import Serializable


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

        query = GetDevicesQuery(
            device_ids=device_ids,
            region_id=region_id)

        results = self.collection.find(
            query.get_filter())

        return await results.to_list(
            length=None)

    async def get_devices_ids_by_region(
        self,
        region_id
    ):
        '''
        Get device IDs tied to the provided reg
        '''

        if none_or_whitespace(region_id):
            NullArgumentException.if_none_or_whitespace(
                region_id, 'region_id')

        query = GetDevicesByRegionQuery(
            region_id=region_id)

        results = self.collection.find(
            query.get_filter(),
            query.get_projection())

        return await results.to_list(
            length=None)

    async def get_automated_sync_devices(
        self
    ):
        '''
        Get devices flagged for automatic sync
        '''

        results = self.collection.find({
            'device_sync': True
        })

        return await results.to_list(
            length=None)
