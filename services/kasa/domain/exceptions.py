from framework.validators.nulls import none_or_whitespace


class NotFoundException(Exception):
    def __init__(self, object_name, object_id, *args: object) -> None:
        super().__init__(f"No {object_name} with the ID '{object_id}' exists")


class RequiredFieldException(Exception):
    def __init__(self, field_name, *args: object, **kwargs) -> None:
        super().__init__(f"Value is required for field: {field_name}")


class RequiredRouteSegmentException(Exception):
    def __init__(self, segment_name, *args: object, **kwargs) -> None:
        super().__init__(f"Route segment '{segment_name}' is required")

    @staticmethod
    def if_none(value, arg_name):
        if value is None:
            raise RequiredRouteSegmentException(arg_name)

    @staticmethod
    def if_none_or_whitespace(value, arg_name):
        if none_or_whitespace(value):
            raise RequiredRouteSegmentException(arg_name)


class RegionNotFoundException(Exception):
    def __init__(self, region_id, *args: object) -> None:
        super().__init__(f"No region with the ID '{region_id}' exists")


class RegionExistsException(Exception):
    def __init__(self, region_name, *args: object) -> None:
        super().__init__(f"A region with the name '{region_name}' exists")


class InvalidRegionIdException(Exception):
    def __init__(self, region_id, *args: object) -> None:
        super().__init__(f"Region ID '{region_id}' is not valid")


class InvalidRegionException(Exception):
    def __init__(self, message, *args: object) -> None:
        super().__init__(f"Region is not valid: {message}")


class NoDevicesDefinedForRegionException(Exception):
    def __init__(self, region_id, *args: object) -> None:
        super().__init__(
            f"No devices are defined for region with the ID '{region_id}'")


class InvalidDeviceRequestException(Exception):
    def __init__(self, message, *args: object, **kwargs) -> None:
        super().__init__(f"Device request is not valid: {message}")


class InvalidDeviceTypeException(Exception):
    def __init__(self, device_type, *args: object, **kwargs) -> None:
        super().__init__(f"'{device_type}' is not a known device type")


class InvalidDeviceException(Exception):
    def __init__(self, device_id, *args: object, **kwargs) -> None:
        super().__init__(f"Device with the ID '{device_id}' is not valid")


class PresetNotFoundException(NotFoundException):
    def __init__(self, preset_id, *args: object) -> None:
        super().__init__(
            object_name='preset',
            object_id=preset_id)


class InvalidPresetException(Exception):
    def __init__(self, preset_id, *args: object, **kwargs) -> None:
        super().__init__(f"Preset with the ID '{preset_id}' is not valid")


class SceneNotFoundException(NotFoundException):
    def __init__(self, scene_id, *args: object) -> None:
        super().__init__(
            object_name='scene',
            object_id=scene_id)


class SceneExistsException(Exception):
    def __init__(self, scene_name, *args: object) -> None:
        super().__init__(
            f'Scene with the name {scene_name} already exists')


class SceneCategoryNotFoundException(NotFoundException):
    def __init__(self, scene_category_id, *args: object) -> None:
        super().__init__(
            object_name='scene category',
            object_id=scene_category_id)


class SceneCategoryExistsException(Exception):
    def __init__(self, scene_category_name, *args: object) -> None:
        super().__init__(
            f"A scene category with the name '{scene_category_name}' exists")


class DeviceNotFoundException(Exception):
    def __init__(self, device_id, *args: object) -> None:
        super().__init__(f"No device with the ID '{device_id}' exists")


class NullArgumentException(Exception):
    def __init__(self, arg_name, *args: object) -> None:
        super().__init__(f"Argument '{arg_name}' cannot be null")

    @staticmethod
    def if_none(value, arg_name):
        if value is None:
            raise NullArgumentException(arg_name)

    @staticmethod
    def if_none_or_whitespace(value, arg_name):
        if none_or_whitespace(value):
            raise NullArgumentException(arg_name)


class PresetExistsException(Exception):
    def __init__(self, preset_name, *args: object) -> None:
        super().__init__(
            f"Preset with the name '{preset_name}' already exists")
