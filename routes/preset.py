from framework.logger.providers import get_logger
from framework.rest.blueprints.meta import MetaBlueprint
from quart import request

from services.kasa_preset_service import (CreatePresetRequest,
                                          KasaPresetSevice,
                                          UpdatePresetRequest)

logger = get_logger(__name__)

preset_bp = MetaBlueprint('preset_bp', __name__)


@preset_bp.configure('/api/preset/<id>', methods=['GET'], auth_scheme='read')
async def get_preset(container, id):
    kasa_preset_service: KasaPresetSevice = container.resolve(
        KasaPresetSevice)

    logger.info(f'Get preset: {id}')
    result = await kasa_preset_service.get_preset(
        preset_id=id)

    return result.to_dict()


@preset_bp.configure('/api/preset/<preset_id>', methods=['DELETE'], auth_scheme='write')
async def delete_preset(container, preset_id):
    kasa_preset_service: KasaPresetSevice = container.resolve(
        KasaPresetSevice)

    result = await kasa_preset_service.delete_preset(
        preset_id=preset_id)

    return result.to_dict()


@preset_bp.configure('/api/preset', methods=['GET'],  auth_scheme='read')
async def get_all(container):
    kasa_preset_service: KasaPresetSevice = container.resolve(
        KasaPresetSevice)

    result = await kasa_preset_service.get_all_presets()

    return {
        'presets': [
            obj.to_dict()
            for obj in result
        ]
    }


@preset_bp.configure('/api/preset', methods=['POST'],  auth_scheme='write')
async def create_preset(container):
    kasa_preset_service: KasaPresetSevice = container.resolve(
        KasaPresetSevice)

    body = await request.get_json()
    result = await kasa_preset_service.create_preset(
        request=CreatePresetRequest(
            body=body))

    return result.to_dict()


@preset_bp.configure('/api/preset', methods=['PUT'],  auth_scheme='write')
async def update_preset(container):
    kasa_preset_service: KasaPresetSevice = container.resolve(
        KasaPresetSevice)

    body = await request.get_json()
    result = await kasa_preset_service.update_preset(
        request=UpdatePresetRequest(
            body=body))

    return result.to_dict()
