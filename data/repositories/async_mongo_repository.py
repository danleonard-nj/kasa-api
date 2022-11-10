from typing import Any, List

from motor.core import AgnosticCollection, AgnosticDatabase
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult


class MongoRepositoryAsync:
    def __init__(
        self,
        client,
        database: str,
        collection: str
    ) -> None:
        '''
        Create an async Mongo repository with basic
        CRUD methods
        '''

        self.__client = client
        self.__database: AgnosticDatabase = self.__client.get_database(
            database)
        self.__collection: AgnosticCollection = self.__database.get_collection(
            collection)

    @property
    def collection(self):
        return self.__collection

    async def insert(
        self,
        document: dict
    ) -> InsertOneResult:
        '''
        Insert a document
        '''

        result = await self.__collection.insert_one(document)
        return result

    async def update(
        self,
        selector: dict,
        values: dict
    ) -> UpdateResult:
        '''
        Update a document
        '''

        result = await self.__collection.update_one(
            filter=selector,
            update={'$set': values})
        return result

    async def replace(
        self,
        selector: dict,
        document: dict
    ) -> UpdateResult:
        '''
        Replace a document
        '''

        result = await self.__collection.replace_one(
            filter=selector,
            replacement=document)
        return result

    async def delete(
        self,
        selector: dict
    ) -> DeleteResult:
        '''
        Delete a document
        '''

        result = await self.__collection.delete_one(
            filter=selector)
        return result

    async def get(
        self,
        selector: dict
    ) -> Any:
        '''
        Get a document
        '''

        result = await self.__collection.find_one(
            filter=selector)
        return result

    async def get_all(
        self
    ) -> List[Any]:
        '''
        Get all documents from collection
        '''

        result = self.__collection.find({})

        docs = []
        async for doc in result:
            docs.append(doc)
        return docs

    async def query(
            self,
            filter: dict
    ) -> list[dict]:
        '''
        Query the collection
        '''

        return list(await self.__collection.find(filter))
