import asyncio
from functools import wraps
import json
from datetime import datetime
from typing import List
from unittest.mock import Mock

from domain.constants import KasaDeviceType
from framework.auth.wrappers.azure_ad_wrappers import azure_ad_authorization
from framework.dependency_injection.provider import inject_container_async
from framework.handlers.response_handler_async import response_handler
from framework.logger.providers import get_logger
from framework.testing.helpers import guid
from quart import Blueprint

logger = get_logger(__name__)


def apply(items, func):
    return list(map(func, items))


def none_or_whitespace(value: str):
    return value is None or value == ''


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


def select(items, func):
    return [func(item) for item in items]


def get_test_data(name):
    with open(f'./tests/data/{name}', 'r') as file:
        return json.loads(file.read())


# class MockRequestProvider:
#     def get_delete_response(self, deleted_count):
#         delete_result = Mock()

#         delete_result.acknowledged = True
#         delete_result.raw_result = dict()
#         delete_result.deleted_count = deleted_count

#         return DeleteResponse(
#             delete_result=delete_result)


class TestData:
    def get_delete_result(self, deleted_count=1):
        delete_result = Mock()

        delete_result.acknowledged = True
        delete_result.raw_result = dict()
        delete_result.deleted_count = deleted_count
        return delete_result

    def get_preset(self):
        return {
            'preset_id': guid(),
            'preset_name': guid(),
            'device_type': KasaDeviceType.KasaLight,
            'definition': {
                'brightness': 100,
                'hue': 272,
                'saturation': 43,
                'state': True,
                'temperature': 0
            }
        }

    def get_preset_definition(self):
        return {
            'brightness': 100,
            'hue': 272,
            'saturation': 43,
            'state': True,
            'temperature': 0
        }

    def get_light_device(self):
        return {
            'state': True,
            'device_id': guid(),
            'device_type': KasaDeviceType.KasaLight,
            'device_name': guid(),
            'brightness': 100,
            'hue': 100,
            'saturation': 100,
            'temperature': 100
        }

    def get_kasa_light_device(self):
        return {
            "deviceType": "IOT.SMARTBULB",
            "role": 0,
            "fwVer": "1.0.11 Build 210915 Rel.085228",
            "appServerUrl": "https://use1-wap.tplinkcloud.com",
            "deviceRegion": "us-east-1",
            "deviceId": guid(),
            "deviceName": guid(),
            "deviceHwVer": "3.0",
            "alias": guid(),
            "deviceMac": guid(),
            "oemId": guid(),
            "deviceModel": "KL130(US)",
            "hwId": guid(),
            "fwId": "00000000000000000000000000000000",
            "isSameRegion": True,
            "status": 1
        }

    def get_kasa_client_token_response(self, token=None):
        return {
            "error_code": 0,
            "result": {
                "accountId": guid(),
                "regTime": datetime.now().isoformat(),
                "riskDetected": 0,
                "email": guid(),
                "token": token or guid()
            }
        }

    def get_device(self):
        return {
            'device_id': guid(),
            'device_name': guid(),
            'device_type': KasaDeviceType.KasaLight,
            'preset_id': guid()
        }

    # def get_event_message(self):
    #     return EventMessage(
    #         endpoint=guid(),
    #         method=guid(),
    #         body=guid(),
    #         info=guid(),
    #         verify_endpoint=False)

    def get_scene(self):
        return {
            "flow": [{
                "data": {
                    "label": "Plug Off"
                },
                "id": "a7d25728-6e67-4a5e-8114-250a21b2662f",
                "position": {
                    "x": -195,
                    "y": 21
                },
                "type": "input"
            },
                {
                    "data": {
                        "label": "Bedroom Bathroom Wax Melter"
                    },
                    "id": "800695141FED00F88FB3140FA384F6991DA9B522",
                    "position": {
                        "x": -123,
                        "y": 177
                    },
                    "type": "output"
            },
                {
                    "animated": True,
                    "id": "reactflow__edge-a7d25728-6e67-4a5e-8114-250a21b2662fnull-800695141FED00F88FB3140FA384F6991DA9B522null",
                    "source": "a7d25728-6e67-4a5e-8114-250a21b2662f",
                    "sourceHandle": None,
                    "target": "800695141FED00F88FB3140FA384F6991DA9B522",
                    "targetHandle": None
            }],
            "mapping": [{
                "devices": [
                        "800695141FED00F88FB3140FA384F6991DA9B522"
                        ],
                "preset_id": "a7d25728-6e67-4a5e-8114-250a21b2662f"
            }],
            "scene_id": guid(),
            "scene_name": guid()
        }


def get_mock_async_result(value):
    future = asyncio.Future()
    future.set_result(value)
    return future
