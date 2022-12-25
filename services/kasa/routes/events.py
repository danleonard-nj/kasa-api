from framework.rest.blueprints.meta import MetaBlueprint
from quart import request

from providers.kasa_client_response_provider import KasaClientResponseProvider

events_bp = MetaBlueprint('events_bp', __name__)


@events_bp.configure('/api/event/device/response', methods=['POST'], auth_scheme='execute')
async def post_event_device_response(container):
    provider: KasaClientResponseProvider = container.resolve(
        KasaClientResponseProvider)

    body = await request.get_json()

    return await provider.update_client_response(
        body=body)
