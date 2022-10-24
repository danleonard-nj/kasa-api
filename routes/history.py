from framework.auth.wrappers.azure_ad_wrappers import azure_ad_authorization
from framework.handlers.response_handler_async import response_handler
from framework.dependency_injection.provider import inject_container_async
from framework.logger.providers import get_logger
from quart import Blueprint
from services.kasa_history_service import KasaHistoryService

logger = get_logger(__name__)
history_bp = Blueprint('history_bp', __name__)


@history_bp.route('/api/history/device/<device_id>', methods=['GET'], endpoint='get_device_history')
@response_handler
@azure_ad_authorization(scheme='read')
@inject_container_async
async def get_device_history(container, device_id):
    service: KasaHistoryService = container.resolve(
        KasaHistoryService)

    result = await service.get_device_history(
        device_id=device_id
    )

    return result


@history_bp.route('/api/history/device', methods=['GET'], endpoint='get_all_device_history')
@response_handler
@azure_ad_authorization(scheme='read')
@inject_container_async
async def get_all_device_history(container):
    service: KasaHistoryService = container.resolve(
        KasaHistoryService)

    result = await service.get_all_device_history()

    return {
        'history': [
            obj.to_dict() for obj in result
        ]
    }


@history_bp.route('/api/history/device/<device_id>/preset/<preset_id>', methods=['POST'], endpoint='post_device_history')
@response_handler
@azure_ad_authorization(scheme='write')
@inject_container_async
async def post_device_history(container, device_id, preset_id):
    service: KasaHistoryService = container.resolve(
        KasaHistoryService)

    result = await service.store_device_history(
        device_id=device_id,
        preset_id=preset_id)

    return result
