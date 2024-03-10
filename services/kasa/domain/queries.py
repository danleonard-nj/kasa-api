from abc import abstractmethod
from typing import Dict, List

from framework.serialization import Serializable
from framework.validators.nulls import none_or_whitespace


class Queryable(Serializable):
    @abstractmethod
    def get_query(self):
        pass

    def get_projection(
        self
    ):
        return None

    def get_sort(
        self
    ) -> list:
        return []


class GetDevicesQuery(Queryable):
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

    def _get_device_filter(
        self
    ) -> Dict:
        return {
            'device_id': {
                '$in': self.device_ids}
        }

    def get_query(
        self
    ) -> Dict:
        query_filter = self._get_device_filter()

        if self.is_region_query:
            return query_filter | {
                'region_id': self.region_id
            }

        return self._get_device_filter()


class GetDevicesByRegionQuery(Queryable):
    def __init__(
        self,
        region_id: str
    ):
        self.region_id = region_id

    def get_query(
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


class GetPresetsByPresetIdsQuery(Queryable):
    def __init__(
        self,
        preset_ids: List[str]
    ):
        self.preset_ids = preset_ids

    def get_query(
        self
    ) -> dict:
        return {
            'preset_id': {
                '$in': self.preset_ids
            }
        }
