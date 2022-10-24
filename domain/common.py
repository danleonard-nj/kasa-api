import base64
from datetime import datetime
import hashlib
import uuid

from framework.serialization import Serializable
from framework.serialization.utilities import serialize


class Hashable:
    def get_hash(self):
        hash_value = hashlib.sha256(serialize(
            self.__dict__).encode()).digest()
        return base64.b64encode(hash_value).decode()


class KasaRegion(Serializable):
    def __init__(self, data):
        self.region_id = data.get('region_id')
        self.region_name = data.get('region_name')
        self.region_description = data.get('region_description')
        self.created_date = data.get('created_date')

    @staticmethod
    def create_region(
        region_name: str,
        region_description: str
    ) -> 'KasaRegion':
        return KasaRegion({
            'region_id': str(uuid.uuid4()),
            'region_name': region_name,
            'region_description': region_description,
            'created_date': datetime.utcnow()
        })
