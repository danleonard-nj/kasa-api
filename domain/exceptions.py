
class RequiredFieldException(Exception):
    def __init__(self, field_name, *args: object, **kwargs) -> None:
        super().__init__(f"Value is required for field: {field_name}")


class RequiredRouteSegmentException(Exception):
    def __init__(self, segment_name, *args: object, **kwargs) -> None:
        super().__init__(f"Route segment '{segment_name}' is required")


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


class InvalidDeviceRequestException(Exception):
    def __init__(self, message, *args: object, **kwargs) -> None:
        super().__init__(f"Device request is not valid: {message}")
