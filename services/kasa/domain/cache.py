from framework.validators.nulls import none_or_whitespace
from framework.crypto.hashing import sha256


class CacheKey:
    @staticmethod
    def preset_key(preset_id):
        return f'preset-{preset_id}'

    @staticmethod
    def preset_list():
        return f'preset-list'

    @staticmethod
    def device_key(device_id):
        return f'device-{device_id}'

    @staticmethod
    def device_list():
        return 'device-list'

    @staticmethod
    def kasa_token():
        return f'kasa-token'

    @staticmethod
    def kasa_request(preset_id, device_id):
        return f'preset-{preset_id}-device-{device_id}-request'

    @staticmethod
    def event_token():
        return f'event-token'

    @staticmethod
    def scene_key(scene_id):
        return f'scene-{scene_id}'

    @staticmethod
    def auth_token(
        client: str,
        scope: str = None
    ) -> str:
        if not none_or_whitespace(scope):
            hashed_scope = sha256(scope)
            return f'auth-{client}-{hashed_scope}'
        return f'auth-{client}'

    @staticmethod
    def scene_list():
        return 'scene-list'

    @staticmethod
    def device_state(device_id, preset_id):
        return f'device-state-{device_id}-{preset_id}'


class CacheExpiration:
    @staticmethod
    def hours(hours):
        return hours * 60

    @staticmethod
    def days(days):
        return days * 24 * 60

    @staticmethod
    def minutes(minutes):
        return minutes


class Cacheable:
    @classmethod
    def cache_key(cls, object_id):
        raise NotImplementedError()
