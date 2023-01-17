import json
from typing import Dict

from framework.serialization import Serializable
from framework.validators.nulls import none_or_whitespace
from pymongo.results import DeleteResult

from domain.constants import KasaRequestMethod, KasaRest
from domain.exceptions import RequiredFieldException


class ApiRequest:
    def required_fields(self):
        return []

    def validate(self):
        for field in self.required_fields():
            if none_or_whitespace(getattr(self, field)):
                raise RequiredFieldException(field)


class KasaRequestBase(Serializable):
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

    def __init__(
        self,
        data: dict
    ):
        self.data = data

        self.error_code = data.get(
            'error_code') or 0
        self.error_message = data.get(
            'msg')

    def serializer_exclude(self):
        return ['data']


class KasaRequest(Serializable):
    def __init__(self, data):
        self.device_id = data.get('device_id')
        self.preset_id = data.get('preset_id')
        self.request_body = data.get('request_body')

    def get_request_body(self):
        return self.request_body

    def to_string(self):
        return json.dumps(self.json, indent=True)


class CreateSceneRequest(ApiRequest, Serializable):
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


class UpdateSceneRequest(ApiRequest, Serializable):
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


class GetPresetRequest(ApiRequest, Serializable):
    def __init__(self, data):
        self.preset_id = data.get('preset_id')
        self.device_id = data.get('device_id')
        self.validate()

    def required_fields(self):
        return ['preset_id',
                'device_id']


class RunSceneRequest(ApiRequest, Serializable):
    '''
    Request for triggering a scene

    `scene_id`: scene to trigger
    '''

    def __init__(
        self,
        scene_id: str,
        region_id: str,
        request
    ):
        self.scene_id = scene_id
        self.region_id = region_id
        self.momentary = request.args.get('momentary') == 'true'
        self.validate()

    def required_fields(self):
        return ['scene_id']


class GetDevicesRequest(Serializable):
    def to_dict(self):
        return {
            'method': KasaRest.GET_DEVICE_LIST
        }


class KasaTokenRequest(ApiRequest, Serializable):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.validate()

    def to_dict(self):
        return {
            KasaRest.METHOD: KasaRequestMethod.LOGIN,
            KasaRest.PARAMS: {
                KasaRest.APP_TYPE: KasaRest.ANDROID,
                KasaRest.USERNAME: self.username,
                KasaRest.PASSWORD: self.password,
                KasaRest.TERMINAL_ID: '43224'
            }
        }

    def required_fields(self):
        return ['username',
                'password']


class MappedSceneRequest(ApiRequest, Serializable):
    def __init__(self, device_id, preset_id):
        self.device_id = device_id
        self.preset_id = preset_id
        self.validate()

    def required_fields(self):
        return ['device_id',
                'preset_id']


class CreatePresetRequest(ApiRequest, Serializable):
    def __init__(
        self,
        body: dict
    ):
        self.body = body
        self.validate()

    def required_fields(self):
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
    def device_list(self):
        return (self.response.result.get(
            KasaRest.DEVICE_LIST)
            if self.response.has_result
            else list())


class SetDevicePresetResponse(Serializable):
    def __init__(
        self,
        kasa_request,
        kasa_response
    ):
        self.kasa_request = kasa_request
        self.kasa_response = kasa_response

    def to_dict(
        self
    ) -> Dict:
        return {
            'request': self.kasa_request.to_dict(),
            'response': self.kasa_response.to_dict()
        }


class KasaTokenResponse(KasaResponse):
    def __init__(self, data):
        super().__init__(data)

        token = (self.result.get('token')
                 if self.has_result
                 else None)
        self.token = token


class GetKasaDeviceStateRequest(KasaRequestBase):
    def __init__(self, device_id):
        super().__init__(
            device_id,
            self.get_request_data())

    def get_request_data(self):
        return {
            KasaRest.SYSTEM: {
                KasaRest.GET_SYSINFO: None
            }
        }


class CreateRegionRequest(ApiRequest, Serializable):
    def __init__(self, data):
        self.region_name = data.get('region_name')
        self.region_description = data.get('region_description')
        self.validate()

    def required_fields(self):
        return ['region_name',
                'region_description']


class UpdateDeviceRequest(ApiRequest, Serializable):
    def __init__(self, data):
        self.device_id = data.get('device_id')
        self.device_name = data.get('device_name')
        self.device_type = data.get('device_type')
        self.region_id = data.get('region_id')
        self.validate()

    def required_fields(self):
        return ['device_id',
                'device_name',
                'device_type',
                'region_id']


class CreateSceneCategoryRequest:
    def __init__(self, data):
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
