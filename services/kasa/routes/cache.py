from framework.logger.providers import get_logger
from framework.rest.blueprints.meta import MetaBlueprint
from quart import request

from services.kasa_device_service import KasaDeviceService

logger = get_logger(__name__)
cache_bp = MetaBlueprint('cache_bp', __name__)


@cache_bp.configure('/api/cache/device/purge', methods=['POST'], auth_scheme='write')
async def post_purge_device_cache(container):
    kasa_device_service: KasaDeviceService = container.resolve(
        KasaDeviceService)

    region_id = request.args.get('region_id')

    result = await kasa_device_service.clear_cache_by_region(
        region_id=region_id)

    return result


@cache_bp.configure('/api/cache/purge', methods=['POST'], auth_scheme='write')
async def post_purge_cache(container):
    kasa_device_service: KasaDeviceService = container.resolve(
        KasaDeviceService)

    result = await kasa_device_service.clear_cache()

    return {
        'keys': result
    }
