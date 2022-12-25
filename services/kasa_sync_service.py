from framework.configuration import Configuration

from services.kasa_client_response_service import KasaClientResponseService
from services.kasa_device_service import KasaDeviceService
from framework.logger import get_logger
from framework.exceptions.nulls import ArgumentNullException

logger = get_logger(__name__)


class KasaSyncService:
    def __init__(
        self,
        configuration: Configuration,
        device_service: KasaDeviceService
    ):
        self.__configuration = configuration
        self.__device_service = device_service

    async def get_device_active_preset(
        self,
        device_id: str
    ):
        ArgumentNullException.if_none_or_whitespace(device_id, 'device_id')

        logger.info(f'Fetching device record')
        device = await self.__device_service.get_device(
            device_id=device_id)

        logger.info(f'Fetching current device state')
        device_state = await self.__device_service.get_device_state(
            device_id=device_id)

    def sync_device(
        self,
        device_id
    ):
        pass

    async def run_automated_device_sync(
        self
    ):
        logger.info('Starting automated sync process')
        auto_sync_devices = await self.__device_service.get_auto_sync_enabled_devices()

        logger.info(f'Autosync devices: {len(auto_sync_devices)}')

        if not any(auto_sync_devices):
            logger.info('No devices configured for autosync')
            return
