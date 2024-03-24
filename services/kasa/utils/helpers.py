import datetime
import json
import time
from framework.crypto.hashing import sha256
from dateutil import parser


def get_map(items: list, key: str, is_dict: bool = True):
    if is_dict:
        return {
            item.get(key): item
            for item in items
        }

    else:
        return {
            getattr(item, key): item
            for item in items
        }


def generate_key(items):
    return sha256(
        data=json.dumps(
            items,
            default=str
        )
    )


class DateTimeUtil:
    @staticmethod
    def timestamp() -> int:
        return int(time.time())

    @staticmethod
    def parse(date_string: str) -> datetime.datetime:
        return parser.parse(date_string)

    @staticmethod
    def now(tz=datetime.UTC) -> datetime.datetime:
        return datetime.datetime.now(tz=tz)

    @classmethod
    def iso(cls, tz=datetime.UTC):
        return cls.now(tz=tz).isoformat()
