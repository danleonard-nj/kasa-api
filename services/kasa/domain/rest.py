import json
from typing import Dict

from domain.constants import KasaRest
from domain.exceptions import RequiredFieldException
from framework.serialization import Serializable
from framework.validators.nulls import none_or_whitespace
from httpx import Response
from pymongo.results import DeleteResult


class Validatable:
    def required_fields(self):
        return []

    def validate(self):
        for field in self.required_fields():
            if none_or_whitespace(getattr(self, field)):
                raise RequiredFieldException(field)


class KasaApiRequest(Serializable):
    def __init__(
        self,
        device_id: str,
        request_data: Dict,
        method: str = 'passthrough'
    ):
        self.method = method
        self.device_id = device_id
        self.request_data = request_data

    def to_dict(self):
        return {
            'method': self.method,
            'params': {
                'deviceId': self.device_id,
                'requestData': self.request_data
            }
        }


class KasaResponse(Serializable):
    @property
    def has_result(
        self
    ) -> bool:
        return 'result' in self.data

    @property
    def is_error(
        self
    ) -> bool:
        return self.error_code < 0

    @property
    def device_object(
        self
    ):
        return self.result.get(
            'responseData').get(
                'system').get(
                    'get_sysinfo')

    @property
    def result(
        self
    ):
        '''
        Kasa response parameter data object
        '''

        if self.has_result:
            return self.data.get('result')

    @property
    def data(
        self
    ):
        '''
        Kasa response data object
        '''

        return self.response.json()

    def __init__(
        self,
        response: Response
    ):

        self.response = response

        data = response.json()
        self.error_code = data.get(
            'error_code') or 0
        self.error_message = data.get(
            'msg')

    @staticmethod
    def empty_response():
        return KasaResponse(Response({}))

    def to_dict(self):
        return super().to_dict() | {
            'response': {
                'status_code': self.response.status_code,
                'duration': f'{self.response.elapsed.total_seconds()}s'
            }
        }


class KasaRequest(Serializable):
    def __init__(self, data):
        self.device_id = data.get('device_id')
        self.preset_id = data.get('preset_id')
        self.request_body = data.get('request_body')

    def get_request_body(self):
        return self.request_body

    def to_string(self):
        return json.dumps(self.json, indent=True)


class CreateSceneRequest(Validatable, Serializable):
    def __init__(self, data):
        self.scene_name = data.get('scene_name')
        self.mapping = data.get('mapping')
        self.flow = data.get('flow')
        self.scene_category_id = data.get('scene_category_id')
        self.validate()

    def required_fields(self):
        return ['scene_name',
                'mapping',
                'flow']


class UpdateSceneRequest(Validatable, Serializable):
    def __init__(self, data):
        self.scene_id = data.get('scene_id')
        self.scene_name = data.get('scene_name')
        self.scene_category_id = data.get('scene_category_id')
        self.mapping = data.get('mapping')
        self.flow = data.get('flow')
        self.validate()

    def required_fields(self):
        return ['scene_id',
                'scene_name',
                'mapping',
                'flow']


class GetPresetRequest(Validatable, Serializable):
    def __init__(self, data):
        self.preset_id = data.get('preset_id')
        self.device_id = data.get('device_id')
        self.validate()

    def required_fields(
        self
    ):
        return ['preset_id',
                'device_id']


class RunSceneRequest(Validatable, Serializable):
    '''
    Request for triggering a scene

    `scene_id`: scene to trigger
    '''

    def __init__(
        self,
        scene_id: str,
        region_id: str,
    ):
        self.scene_id = scene_id
        self.region_id = region_id
        self.validate()

    def required_fields(
        self
    ):
        return ['scene_id']


class GetDevicesRequest(Serializable):
    def to_dict(self):
        return {
            'method': KasaRest.GetDeviceList
        }


class KasaTokenRequest(Validatable, Serializable):
    def __init__(
        self,
        username: str,
        password: str
    ):
        self.username = username
        self.password = password
        self.validate()

    def to_dict(self):
        return {
            'method': 'login',
            'params': {
                'appType': 'Kasa_Android',
                'cloudUserName': self.username,
                'cloudPassword': self.password,
                'terminalUUID': '43224'
            }
        }

    def required_fields(self):
        return ['username',
                'password']


class MappedSceneRequest(Validatable, Serializable):
    def __init__(
        self,
        device_id: str,
        preset_id: str
    ):
        self.device_id = device_id
        self.preset_id = preset_id
        self.validate()

    def required_fields(
        self
    ):
        return ['device_id',
                'preset_id']


class CreatePresetRequest(Validatable, Serializable):
    def __init__(
        self,
        body: dict
    ):
        self.body = body
        self.validate()

    def required_fields(
        self
    ):
        return ['body']


class UpdatePresetRequest(Serializable):
    def __init__(
        self,
        body: dict
    ):
        self.body = body
        self.preset_id = body.get('preset_id')
        self.preset_name = body.get('preset_name')
        self.device_type = body.get('device_type')
        self.definition = body.get('definition')


class DeleteResponse(Serializable):
    def __init__(
        self,
        delete_result: DeleteResult
    ):
        self.deleted_count = delete_result.deleted_count
        self.raw_result = delete_result.raw_result
        self.acknowledged = delete_result.acknowledged


class KasaGetDevicesResponse(Serializable):
    def __init__(
        self,
        data: dict
    ):
        self.response: KasaResponse = data

    @property
    def device_list(
        self
    ):
        return (
            self.response.result.get('deviceList')
            if self.response.has_result
            else list()
        )


class SetDevicePresetResponse(Serializable):
    def __init__(
        self,
        kasa_request,
        kasa_response
    ):
        self.kasa_request = kasa_request
        self.kasa_response = kasa_response


class KasaTokenResponse(KasaResponse):
    def __init__(self, response):
        super().__init__(response)

        token = (self.result.get('token')
                 if self.has_result
                 else None)

        self.token = token


class GetKasaDeviceStateRequest(KasaApiRequest):
    def __init__(
        self,
        device_id: str
    ):
        super().__init__(
            device_id,
            self.get_request_data())

    def get_request_data(
        self
    ):
        return {
            'system': {
                'get_sysinfo': None
            }
        }


class CreateRegionRequest(Validatable, Serializable):
    def __init__(
        self,
        data
    ):
        self.region_name = data.get('region_name')
        self.region_description = data.get('region_description')
        self.validate()

    def required_fields(self):
        return ['region_name',
                'region_description']


class UpdateDeviceRequest(Validatable, Serializable):
    def __init__(
        self,
        data
    ):
        self.device_id = data.get('device_id')
        self.device_name = data.get('device_name')
        self.device_type = data.get('device_type')
        self.region_id = data.get('region_id')
        self.validate()

    def required_fields(
        self
    ):
        return ['device_id',
                'device_name',
                'device_type',
                'region_id']


class CreateSceneCategoryRequest:
    def __init__(
        self,
        data
    ):
        self.scene_category = data.get('scene_category')


class UpdateClientResponseRequest:
    def __init__(self, data):
        self.device_id = data.get('device_id')
        self.preset_id = data.get('preset_id')
        self.client_response = data.get('client_response')
        self.state_key = data.get('state_key')


class SetDeviceStateRequest(Serializable):
    def __init__(
        self,
        data: Dict
    ):
        self.device_id = data.get('device_id')
        self.preset_id = data.get('preset_id')
        self.state_key = data.get('state_key')

    @staticmethod
    def create_request(
        device_id: str,
        preset_id: str,
        state_key: str
    ):
        return SetDeviceStateRequest({
            'device_id': device_id,
            'preset_id': preset_id,
            'state_key': state_key
        })


class DeviceSyncResponse(Serializable):
    def __init__(
        self,
        destructive,
        created,
        removed=None
    ):
        self.destructive = destructive
        self.created = created
        self.removed = removed


class DeleteKasaSceneResponse(Serializable):
    def __init__(
        self,
        modified_count: int
    ):

        self.modified_count = modified_count
