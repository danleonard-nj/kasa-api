
from framework.auth.azure import AzureAd
from clients.cache_client import CacheClientAsync
from framework.configuration.configuration import Configuration
from framework.di.service_collection import ServiceCollection
from framework.di.static_provider import ProviderBase
from motor.motor_asyncio import AsyncIOMotorClient

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
from providers.kasa_device_provider import KasaDeviceProvider
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


def register_clients(descriptors: ServiceCollection):
    descriptors.add_singleton(CacheClientAsync)
    descriptors.add_singleton(IdentityClient)
    descriptors.add_singleton(EventClient)
    descriptors.add_singleton(KasaClient)


def register_repositories(descriptors: ServiceCollection):
    descriptors.add_singleton(KasaSceneRepository)
    descriptors.add_singleton(KasaDeviceRepository)
    descriptors.add_singleton(KasaRegionRepository)
    descriptors.add_singleton(KasaPresetRepository)
    descriptors.add_singleton(KasaClientResponseRepository)
    descriptors.add_singleton(KasaSceneCategoryRepository)


def register_services(descriptors: ServiceCollection):
    descriptors.add_singleton(KasaPresetSevice)
    descriptors.add_singleton(KasaSceneService)
    descriptors.add_singleton(KasaDeviceService)
    descriptors.add_singleton(KasaSceneCategoryService)
    descriptors.add_singleton(KasaExecutionService)
    descriptors.add_singleton(KasaRegionService)
    descriptors.add_singleton(KasaEventService)
    descriptors.add_singleton(KasaClientResponseService)


def register_providers(descriptors: ServiceCollection):
    descriptors.add_singleton(KasaDeviceProvider)


class ContainerProvider(ProviderBase):
    @classmethod
    def configure_container(cls):
        container = ServiceCollection()

        container.add_singleton(Configuration)
        register_clients(container)

        container.add_singleton(
            dependency_type=AsyncIOMotorClient,
            factory=configure_mongo_client)
        container.add_singleton(
            dependency_type=AzureAd,
            factory=configure_azure_ad)

        register_repositories(container)
        register_services(container)
        register_providers(container)

        return container
