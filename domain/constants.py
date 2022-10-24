from utils.constant_base import ConstantBase


class KasaConstant:
    PASSTHROUGH = 'passthrough'
    LOGIN = 'login'


class KasaDeviceType(ConstantBase):
    KasaPlug = 'IOT.SMARTPLUGSWITCH'
    KasaLight = 'IOT.SMARTBULB'


class KasaRequestMethod:
    LOGIN = 'login'
    PASSTHROUGH = 'passthrough'


class KasaRest:
    GET_SYSINFO = 'get_sysinfo'
    RESPONSE_DATA = 'responseData'
    SYSTEM = 'system'
    ERROR_CODE = 'error_code'
    MESSAGE = 'msg'
    RESULT = 'result'
    APP_TYPE = 'appType'
    USERNAME = 'cloudUserName'
    PASSWORD = 'cloudPassword'
    TERMINAL_ID = 'terminalUUID'
    GET_DEVICE_LIST = 'getDeviceList'
    DEVICE_LIST = 'deviceList'
    ANDROID = 'Kasa_Android'
    REQUEST_DATA = 'requestData'
    DEVICE_ID = 'deviceId'
    PARAMS = 'params'
    METHOD = 'method'
    RELAY_STATE = 'relay_state'
    SET_RELAY_STATE = 'set_relay_state'
    STATE = 'state'
    LIGHTING_SERVICE = 'smartlife.iot.smartbulb.lightingservice'
    TRANSITION_LIGHT_STATE = 'transition_light_state'
    MODE = 'mode'
    SATURATION = 'saturation'
    BRIGHTNESS = 'brightness'
    HUE = 'hue'
    ON_OFF = 'on_off'
    COLOR_TEMP = 'color_temp'
    NORMAL = 'normal'
    LIGHT_STATE = 'light_state'
    DEFAULT_LIGHT_STATE = 'dft_on_state'
    IGNORE_DEFAULT = 'ignore_default'


class SemaphoreDefault:
    KASA_CLIENT = 24
