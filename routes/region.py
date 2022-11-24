from framework.logger.providers import get_logger
from quart import request

from domain.rest import CreateRegionRequest
from services.kasa_region_service import KasaRegionService
from utils.meta import MetaBlueprint

logger = get_logger(__name__)
region_bp = MetaBlueprint('region_bp', __name__)


@region_bp.configure('/api/region', methods=['GET'], auth_scheme='read')
async def get_region(container):
    kasa_region_service: KasaRegionService = container.resolve(
        KasaRegionService)

    result = await kasa_region_service.get_regions()

    return result


@region_bp.configure('/api/region', methods=['POST'], auth_scheme='write')
async def create_region(container):
    kasa_region_service: KasaRegionService = container.resolve(
        KasaRegionService)

    body = await request.get_json()
    create_request = CreateRegionRequest(
        data=body)

    result = await kasa_region_service.create_region(
        create_request=create_request)
    return result.to_dict()


@region_bp.configure('/api/region/<region_id>', methods=['DELETE'], auth_scheme='write')
async def delete_region(container):
    kasa_region_service: KasaRegionService = container.resolve(
        KasaRegionService)

    body = await request.get_json()

    create_request = CreateRegionRequest(
        data=body)

    result = await kasa_region_service.create_region(
        create_request=create_request)

    return result.to_dict()
