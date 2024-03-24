from typing import Dict, List

from framework.exceptions.nulls import ArgumentNullException
from framework.mongo.mongo_repository import MongoRepositoryAsync
from motor.motor_asyncio import AsyncIOMotorClient

from data.constants import MongoConstants
from data.queries import GetDeviceLogsByTimestampRangeQuery, GetDevicesByRegionQuery, GetDevicesQuery


class KasaDeviceRepository(MongoRepositoryAsync):
    def __init__(
        self,
        client: AsyncIOMotorClient
    ):
        super().__init__(
            client=client,
            database=MongoConstants.DatabaseName,
            collection=MongoConstants.KasaDeviceCollectionName)

    async def get_device_by_id(
        self,
        device_id: str
    ):
        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')

        result = await self.collection.find_one({
            'device_id': device_id
        })

        return result

    async def get_devices_by_region(
        self,
        region_id: str
    ) -> List[dict]:

        ArgumentNullException.if_none_or_whitespace(region_id, 'region_id')

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
        region_id: str
    ):
        '''
        Get device IDs tied to the provided reg
        '''

        ArgumentNullException.if_none_or_whitespace(region_id, 'region_id')

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


class KasaDeviceLogRepository(MongoRepositoryAsync):
    def __init__(
        self,
        client: AsyncIOMotorClient
    ):
        super().__init__(
            client=client,
            database=MongoConstants.DatabaseName,
            collection=MongoConstants.KasaDeviceLogCollectionName)

    async def get_device_logs_by_timestamp_range(
        self,
        start_timestamp: int,
        end_timestamp: int
    ):
        query = GetDeviceLogsByTimestampRangeQuery(
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp)

        return await (
            self.collection
            .find(query.get_filter())
            .to_list(length=None)
        )
