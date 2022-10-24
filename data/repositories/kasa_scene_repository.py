from data.constants import MongoConstants
from data.repositories.async_mongo_repository import MongoRepositoryAsync


class KasaSceneRepository(MongoRepositoryAsync):
    def __init__(self, container=None):
        self.initialize(
            container=container,
            database=MongoConstants.DatabaseName,
            collection=MongoConstants.KasaSceneCollectionName)

    async def scene_exists(
        self,
        scene_name: str
    ) -> dict:
        '''
        Verify a scene exists by name
        '''

        value = await self.get({
            'scene_name': scene_name
        })

        return value is not None

    async def query(self, filter: dict) -> list[dict]:
        result = self.collection.find(filter)
        return await result.to_list(length=None)
