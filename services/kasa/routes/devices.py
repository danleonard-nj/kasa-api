from framework.logger.providers import get_logger
from quart import request

from providers.kasa_device_provider import KasaDeviceProvider
from utils.meta import MetaBlueprint

logger = get_logger(__name__)
devices_bp = MetaBlueprint('devices_bp', __name__)


@devices_bp.configure('/api/device', methods=['GET'], auth_scheme='read')
async def get_devices(container):
    kasa_device_provider: KasaDeviceProvider = container.resolve(
        KasaDeviceProvider)

    return await kasa_device_provider.get_all_devices()


@devices_bp.configure('/api/device', methods=['PUT'], auth_scheme='write')
async def update_device(container):
    kasa_device_provider: KasaDeviceProvider = container.resolve(
        KasaDeviceProvider)

    body = await request.get_json()

    return await kasa_device_provider.update_device(
        body=body)


@devices_bp.configure('/api/device/<device_id>', methods=['GET'], auth_scheme='read')
async def get_device(container, device_id):
    kasa_device_provider: KasaDeviceProvider = container.resolve(
        KasaDeviceProvider)

    return await kasa_device_provider.get_device(
        device_id=device_id)


@devices_bp.configure('/api/device/sync', methods=['POST'], auth_scheme='write')
async def sync_devices(container):
    kasa_device_provider: KasaDeviceProvider = container.resolve(
        KasaDeviceProvider)

    return await kasa_device_provider.sync_devices()


@devices_bp.configure('/api/device/<device_id>/preset/<preset_id>', methods=['POST'], auth_scheme='write')
async def set_device_preset(container, device_id: str, preset_id: str):
    kasa_device_provider: KasaDeviceProvider = container.resolve(
        KasaDeviceProvider)

    return await kasa_device_provider.set_device_preset(
        device_id=device_id,
        preset_id=preset_id)


@devices_bp.configure('/api/device/<device_id>/region/<region_id>', methods=['POST'], auth_scheme='write')
async def set_device_region(container, device_id: str, region_id: str):
    kasa_device_provider: KasaDeviceProvider = container.resolve(
        KasaDeviceProvider)

    return await kasa_device_provider.set_device_region(
        device_id=device_id,
        region_id=region_id)


@devices_bp.configure('/api/device/<device_id>/response', methods=['GET'], auth_scheme='read')
async def get_device_client_response(container, device_id: str):
    kasa_device_provider: KasaDeviceProvider = container.resolve(
        KasaDeviceProvider)

    return await kasa_device_provider.get_device_client_response(
        device_id=device_id)
