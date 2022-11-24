
from framework.abstractions.abstract_request import RequestContextProvider
from framework.auth.azure import AzureAd
from framework.clients.cache_client import CacheClientAsync
from framework.configuration.configuration import Configuration
from framework.di.service_collection import ServiceCollection
from framework.di.static_provider import ProviderBase
from motor.motor_asyncio import AsyncIOMotorClient
from quart import Quart, request

from clients.identity_client import IdentityClient
from clients.kasa_client import KasaClient
from clients.service_bus import EventClient
from data.repositories.kasa_client_response_repository import \
    KasaClientResponseRepository
from data.repositories.kasa_device_repository import KasaDeviceRepository
from data.repositories.kasa_preset_repository import KasaPresetRepository
from data.repositories.kasa_region_repository import KasaRegionRepository
from data.repositories.kasa_scene_category_repository import \
    KasaSceneCategoryRepository
from data.repositories.kasa_scene_repository import KasaSceneRepository
from domain.kasa.auth import configure_azure_ad
from services.kasa_client_response_service import KasaClientResponseService
from services.kasa_device_service import KasaDeviceService
from services.kasa_event_service import KasaEventService
from services.kasa_execution_service import KasaExecutionService
from services.kasa_preset_service import KasaPresetSevice
from services.kasa_region_service import KasaRegionService
from services.kasa_scene_category_service import KasaSceneCategoryService
from services.kasa_scene_service import KasaSceneService


def configure_mongo_client(container):
    configuration = container.resolve(Configuration)

    connection_string = configuration.mongo.get('connection_string')
    client = AsyncIOMotorClient(connection_string)

    return client


class ContainerProvider(ProviderBase):
    @classmethod
    def configure_container(cls):
        container = ServiceCollection()

        container.add_singleton(Configuration)

        # Clients
        container.add_singleton(CacheClientAsync)
        container.add_singleton(IdentityClient)
        container.add_singleton(EventClient)
        container.add_singleton(KasaClient)

        container.add_singleton(
            dependency_type=AsyncIOMotorClient,
            factory=configure_mongo_client)
        container.add_singleton(
            dependency_type=AzureAd,
            factory=configure_azure_ad)

        # Repositories
        container.add_singleton(KasaSceneRepository)
        container.add_singleton(KasaDeviceRepository)
        container.add_singleton(KasaRegionRepository)
        container.add_singleton(KasaPresetRepository)
        container.add_singleton(KasaClientResponseRepository)
        container.add_singleton(KasaSceneCategoryRepository)

        # Services
        container.add_singleton(KasaPresetSevice)
        container.add_singleton(KasaSceneService)
        container.add_singleton(KasaDeviceService)
        container.add_singleton(KasaSceneCategoryService)
        container.add_singleton(KasaExecutionService)
        container.add_singleton(KasaRegionService)
        container.add_singleton(KasaEventService)
        container.add_singleton(KasaClientResponseService)

        return container
