from typing import Dict, Union
from framework.mongo.mongo_repository import MongoRepositoryAsync
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.results import DeleteResult

from data.constants import MongoConstants


class KasaSceneRepository(MongoRepositoryAsync):
    def __init__(
        self,
        client: AsyncIOMotorClient
    ):
        super().__init__(
            client=client,
            database=MongoConstants.DatabaseName,
            collection=MongoConstants.KasaSceneCollectionName)

    async def delete_scene_by_id(
        self,
        scene_id: str
    ) -> DeleteResult:

        return await self.delete({
            'scene_id': scene_id
        })

    async def get_scene_by_id(
        self,
        scene_id: str
    ) -> Union[Dict, None]:

        return await self.get({
            'scene_id': scene_id
        })

    async def scene_exists(
        self,
        scene_name: str
    ) -> bool:

        value = await self.get({
            'scene_name': scene_name
        })

        return value is not None

    async def query(
        self,
        filter: dict
    ) -> list[dict]:

        result = self.collection.find(filter)
        return await result.to_list(length=None)
