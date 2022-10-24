from data.constants import MongoConstants
from data.repositories.async_mongo_repository import MongoRepositoryAsync


class KasaDeviceHistoryRepository(MongoRepositoryAsync):
    def __init__(self, container=None):
        self.initialize(
            container=container,
            database=MongoConstants.DatabaseName,
            collection=MongoConstants.KasaDeviceHistoryCollectionName)
