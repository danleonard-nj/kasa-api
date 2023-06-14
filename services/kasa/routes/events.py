from framework.rest.blueprints.meta import MetaBlueprint
from quart import request

from domain.kasa.auth import AuthPolicy
from providers.kasa_client_response_provider import KasaClientResponseProvider
from providers.kasa_device_state_provider import KasaDeviceStateProvider

events_bp = MetaBlueprint('events_bp', __name__)


@events_bp.configure('/api/event/device/response', methods=['POST'], auth_scheme=AuthPolicy.Execute)
async def post_event_device_response(container):
    provider: KasaClientResponseProvider = container.resolve(
        KasaClientResponseProvider)

    body = await request.get_json()

    return await provider.update_client_response(
        body=body)


@events_bp.configure('/api/event/device/state', methods=['POST'], auth_scheme=AuthPolicy.Execute)
async def post_event_device_state(container):
    provider: KasaDeviceStateProvider = container.resolve(
        KasaDeviceStateProvider)

    body = await request.get_json()

    return await provider.update_client_response(
        body=body)
