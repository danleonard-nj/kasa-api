from abc import abstractmethod
from typing import Dict, List

from framework.serialization import Serializable
from framework.validators.nulls import none_or_whitespace


class MongoProjectionQuery(Serializable):
    @abstractmethod
    def get_filter(
        self
    ):
        pass

    @abstractmethod
    def get_projection(
        self
    ):
        pass


class MongoQuery(Serializable):
    @abstractmethod
    def get_filter(self):
        pass


class GetDevicesQuery(MongoQuery):
    @property
    def is_region_query(
        self
    ):
        return not none_or_whitespace(
            self.region_id)

    def __init__(
        self,
        device_ids: List[str],
        region_id: str = None
    ):
        self.device_ids = device_ids
        self.region_id = region_id

    def __get_device_filter(
        self
    ) -> Dict:
        return {
            'device_id': {
                '$in': self.device_ids}
        }

    def get_filter(
        self
    ) -> Dict:
        query_filter = self.__get_device_filter()

        if self.is_region_query:
            return query_filter | {
                'region_id': self.region_id
            }

        return self.__get_device_filter()


class GetDevicesByRegionQuery(MongoProjectionQuery):
    def __init__(
        self,
        region_id: str
    ):
        self.region_id = region_id

    def get_filter(
        self
    ):
        return {
            'region_id': self.region_id
        }

    def get_projection(
        self
    ):
        return {
            'device_id': True,
            '_id': False
        }


class GetDeviceLogsByTimestampRangeQuery(MongoQuery):
    def __init__(
        self,
        start_timestamp: int,
        end_timestamp: int
    ):
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp

    def get_filter(
        self
    ) -> dict:

        return {
            'timestamp': {
                '$gte': self.start_timestamp,
                '$lte': self.end_timestamp
            }
        }
