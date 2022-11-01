from framework.auth.wrappers.azure_ad_wrappers import azure_ad_authorization
from framework.handlers.response_handler_async import response_handler
from framework.dependency_injection.provider import inject_container_async
from framework.logger.providers import get_logger
from quart import Blueprint, request
from services.kasa_preset_service import (CreatePresetRequest,
                                          KasaPresetSevice,
                                          UpdatePresetRequest)

logger = get_logger(__name__)

preset_bp = Blueprint('preset_bp', __name__)


@preset_bp.route('/api/preset/<id>', methods=['GET'], endpoint='get_preset')
@response_handler
@azure_ad_authorization(scheme='read')
@inject_container_async
async def get_preset(container, id):
    kasa_preset_service: KasaPresetSevice = container.resolve(
        KasaPresetSevice)

    logger.info(f'Get preset: {id}')
    result = await kasa_preset_service.get_preset(
        preset_id=id)

    return result.to_dict()


@preset_bp.route('/api/preset/<preset_id>', methods=['DELETE'],  endpoint='delete_preset')
@response_handler
@azure_ad_authorization(scheme='write')
@inject_container_async
async def delete_preset(container, preset_id):
    kasa_preset_service: KasaPresetSevice = container.resolve(
        KasaPresetSevice)

    result = await kasa_preset_service.delete_preset(
        preset_id=preset_id)

    return result.to_dict()


@preset_bp.route('/api/preset', methods=['GET'],  endpoint='get_presets')
@response_handler
@azure_ad_authorization(scheme='read')
@inject_container_async
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


@preset_bp.route('/api/preset', methods=['POST'],  endpoint='create_preset')
@response_handler
@azure_ad_authorization(scheme='write')
@inject_container_async
async def create_preset(container):
    kasa_preset_service: KasaPresetSevice = container.resolve(
        KasaPresetSevice)

    body = await request.get_json()
    result = await kasa_preset_service.create_preset(
        request=CreatePresetRequest(
            body=body))

    return result.to_dict()


@preset_bp.route('/api/preset', methods=['PUT'],  endpoint='update_preset')
@response_handler
@azure_ad_authorization(scheme='write')
@inject_container_async
async def update_preset(container):
    kasa_preset_service: KasaPresetSevice = container.resolve(
        KasaPresetSevice)

    body = await request.get_json()
    result = await kasa_preset_service.update_preset(
        request=UpdatePresetRequest(
            body=body))

    return result.to_dict()
