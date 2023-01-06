from framework.logger.providers import get_logger
from quart import request
from services.kasa_sync_service import KasaSyncService
from utils.meta import MetaBlueprint

logger = get_logger(__name__)
sync_bp = MetaBlueprint('sync_bp', __name__)


@sync_bp.configure('/api/sync/run', methods=['POST'], auth_scheme='write')
async def post_sync_run(container):
    kasa_sync_service: KasaSyncService = container.resolve(
        KasaSyncService)

    result = await kasa_sync_service.run_automated_device_sync()

    return result
