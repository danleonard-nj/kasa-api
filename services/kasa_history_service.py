from typing import List

from data.repositories.kasa_device_history_repository import \
    KasaDeviceHistoryRepository
from domain.kasa.devices.history import DeviceHistory
from framework.logger.providers import get_logger
from framework.serialization.utilities import serialize
from pymongo.results import InsertOneResult, UpdateResult

logger = get_logger(__name__)


class KasaHistoryService:
    def __init__(self, container):
        self.repository: KasaDeviceHistoryRepository = container.resolve(
            KasaDeviceHistoryRepository)

    async def store_device_history(self, history: DeviceHistory):
        logger.info(
            f'Storing device history: {history.device_id}: {history.preset_id}')

        entity = await self.repository.get({
            'device_id': history.device_id
        })

        if entity is None:
            logger.info(
                f'Inserting initial device history for device: {history.device_id}')

            document = history.to_dict()
            insert_result = await self.repository.insert(
                document)

            logger.info(f'Insert result: {insert_result.inserted_id}')
            return self._get_store_history_result(
                result=insert_result,
                document=document)

        logger.info(f'Updating device history for device: {history.device_id}')

        document = history.to_dict()

        update_result = await self.repository.replace(
            selector={'device_id': history.device_id},
            document=document)

        logger.info(f'Device history update: {update_result.upserted_id}')
        return self._get_store_history_result(
            result=update_result,
            document=document)

    def _get_store_history_result(self, result, document):
        return {
            'document': document,
            'action': self.serialize_mongo_result(
                result=result)
        }

    async def get_device_history(self, device_id):
        logger.info(f'Get device history: {device_id}')

        entity = await self.repository.get({
            'device_id': device_id
        })

        if entity is None:
            logger.info(f'No device history exists for device: {device_id}')
            return dict()

        logger.info(f'Device history entity: {serialize(entity)}')
        history = DeviceHistory(
            data=entity)

        return history.to_dict()

    async def get_all_device_history(self) -> List[DeviceHistory]:
        logger.info(f'Get device history')

        entities = await self.repository.get_all()

        history = [
            DeviceHistory(data=entity)
            for entity in entities]

        return history

    def serialize_mongo_result(self, result):
        if isinstance(result, UpdateResult):
            _update_result: UpdateResult = result
            return {
                'type': UpdateResult.__name__,
                'details': {
                    'upserted_id': _update_result.upserted_id,
                    'modified_count': _update_result.modified_count,
                    'matched_count': _update_result.matched_count,
                    'acknowledged': _update_result.acknowledged,
                    'raw_result': _update_result.raw_result
                }
            }

        if isinstance(result, InsertOneResult):
            _insert_result: InsertOneResult = result
            return {
                'type': InsertOneResult.__name__,
                'details': {
                    'inserted_id': _insert_result.inserted_id,
                    'acknowledged': _insert_result.acknowledged,
                }
            }
