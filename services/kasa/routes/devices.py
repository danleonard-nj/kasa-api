from framework.logger.providers import get_logger
from framework.validators.nulls import not_none
from quart import request

from domain.exceptions import RequiredRouteSegmentException
from domain.rest import UpdateDeviceRequest
from services.kasa_device_service import KasaDeviceService
from utils.meta import MetaBlueprint

logger = get_logger(__name__)
devices_bp = MetaBlueprint('devices_bp', __name__)


@devices_bp.configure('/api/device', methods=['GET'], auth_scheme='read')
async def get_devices(container):
    kasa_device_service: KasaDeviceService = container.resolve(
        KasaDeviceService)

    result = await kasa_device_service.get_all_devices()

    return {
        'devices': [
            device.to_display_model()
            for device in result
        ]
    }


@devices_bp.configure('/api/device', methods=['PUT'], auth_scheme='write')
async def update_device(container):
    kasa_device_service: KasaDeviceService = container.resolve(
        KasaDeviceService)

    body = await request.get_json()
    not_none(body)

    update_request = UpdateDeviceRequest(
        data=body)

    result = await kasa_device_service.update_device(
        update_request=update_request)

    return result.to_dict()


@devices_bp.configure('/api/device/<device_id>', methods=['GET'], auth_scheme='read')
async def get_device(container, device_id):
    kasa_device_service: KasaDeviceService = container.resolve(
        KasaDeviceService)

    # Verify device ID
    RequiredRouteSegmentException.if_none_or_whitespace(
        device_id,
        'device_id'
    )

    result = await kasa_device_service.get_device(
        device_id=device_id)

    return result.to_dict()


@devices_bp.configure('/api/device/sync', methods=['POST'], auth_scheme='write')
async def sync_devices(container):
    kasa_device_service: KasaDeviceService = container.resolve(
        KasaDeviceService)

    result = await kasa_device_service.sync_devices()

    return {
        'sync': result
    }


@devices_bp.configure('/api/device/<device_id>/preset/<preset_id>', methods=['POST'], auth_scheme='write')
async def set_device_preset(container, device_id, preset_id):
    kasa_device_service: KasaDeviceService = container.resolve(
        KasaDeviceService)

    # Verify device ID
    RequiredRouteSegmentException.if_none_or_whitespace(
        device_id,
        'device_id'
    )
    # Verify preset ID
    RequiredRouteSegmentException.if_none_or_whitespace(
        preset_id,
        'preset_id'
    )

    kasa_request, kasa_response = await kasa_device_service.set_device_state(
        device_id=device_id,
        preset_id=preset_id)

    return {
        'request': kasa_request,
        'response': kasa_response
    }


@devices_bp.configure('/api/device/state/<device_id>', methods=['GET'], auth_scheme='read')
async def get_device_preset(container, device_id):
    kasa_device_service: KasaDeviceService = container.resolve(
        KasaDeviceService)

    # Verify device ID
    RequiredRouteSegmentException.if_none_or_whitespace(
        device_id,
        'device_id'
    )

    device_state = await kasa_device_service.get_device_state(
        device_id=device_id)

    return device_state.to_dict()


@devices_bp.configure('/api/device/state', methods=['POST'], auth_scheme='execute')
async def set_device_state(container):
    kasa_device_service: KasaDeviceService = container.resolve(
        KasaDeviceService)

    body = await request.get_json()
    not_none(body, 'body')

    result = await kasa_device_service.handle_store_device_state_request(
        data=body)

    return result.to_dict()


@devices_bp.configure('/api/device/state/audit', methods=['POST'], auth_scheme='execute')
async def audit_device_state(container):
    kasa_device_service: KasaDeviceService = container.resolve(
        KasaDeviceService)

    result = await kasa_device_service.audit_device_states()

    return result


@devices_bp.configure('/api/device/<device_id>/region/<region_id>', methods=['POST'], auth_scheme='execute')
async def set_device_region(container, device_id, region_id):
    kasa_device_service: KasaDeviceService = container.resolve(
        KasaDeviceService)

    # Verify device ID
    RequiredRouteSegmentException.if_none_or_whitespace(
        device_id,
        'device_id'
    )
    # Verify region ID
    RequiredRouteSegmentException.if_none_or_whitespace(
        region_id,
        'region_id'
    )

    result = await kasa_device_service.set_device_region(
        device_id=device_id,
        region_id=region_id)

    return result.to_dict()


@devices_bp.configure('/api/device/<id>/response', methods=['GET'], auth_scheme='read')
async def get_device_client_response(container, id):
    kasa_device_service: KasaDeviceService = container.resolve(
        KasaDeviceService)

    result = await kasa_device_service.get_device_client_response(
        device_id=id)

    return result
