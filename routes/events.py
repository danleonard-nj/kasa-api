
from domain.rest import UpdateClientResponseRequest
from framework.rest.blueprints.meta import MetaBlueprint
from quart import request
from services.kasa_client_response_service import KasaClientResponseService

events_bp = MetaBlueprint('events_bp', __name__)


@events_bp.configure('/api/event/device/response', methods=['POST'], auth_scheme='execute')
async def post_event_device_response(container):
    service: KasaClientResponseService = container.resolve(
        KasaClientResponseService)

    body = await request.get_json()
    update_request = UpdateClientResponseRequest(
        data=body)

    result = await service.update_client_response(
        request=update_request)

    return result.to_dict()
