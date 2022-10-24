from multiprocessing import Semaphore
from clients.identity_client import IdentityClient
from clients.kasa_client import KasaClient
from clients.service_bus import QueueClient
from data.repositories.kasa_device_history_repository import \
    KasaDeviceHistoryRepository
from data.repositories.kasa_device_repository import KasaDeviceRepository
from data.repositories.kasa_preset_repository import KasaPresetRepository
from data.repositories.kasa_region_repository import KasaRegionRepository
from data.repositories.kasa_scene_category_repository import KasaSceneCategoryRepository
from data.repositories.kasa_scene_repository import KasaSceneRepository
from domain.kasa.auth import configure_azure_ad
from framework.abstractions.abstract_request import RequestContextProvider
from framework.auth.azure import AzureAd
from framework.clients.cache_client import CacheClientAsync
from framework.clients.http_client import HttpClient
from framework.configuration.configuration import Configuration
from framework.dependency_injection.container import Container
from framework.dependency_injection.provider import ProviderBase
from quart import Quart, request
from services.kasa_device_service import KasaDeviceService
from services.kasa_execution_service import KasaExecutionService
from services.kasa_history_service import KasaHistoryService
from services.kasa_preset_service import KasaPresetSevice
from services.kasa_region_service import KasaRegionService
from services.kasa_scene_service import KasaSceneService


class ContainerProvider(ProviderBase):
    @ classmethod
    def configure_container(cls):
        container = Container()

        container.add_singleton(Configuration)

        # Clients
        container.add_singleton(CacheClientAsync)
        container.add_singleton(IdentityClient)
        container.add_singleton(HttpClient)
        container.add_singleton(QueueClient)
        container.add_singleton(KasaClient)

        container.add_factory_singleton(
            _type=AzureAd,
            factory=configure_azure_ad)

        # Repositories
        container.add_singleton(KasaSceneRepository)
        container.add_singleton(KasaDeviceRepository)
        container.add_singleton(KasaRegionRepository)
        container.add_singleton(KasaPresetRepository)
        container.add_singleton(KasaDeviceHistoryRepository)
        container.add_singleton(KasaSceneCategoryRepository)

        # Services
        container.add_singleton(KasaPresetSevice)
        container.add_singleton(KasaSceneService)
        container.add_singleton(KasaDeviceService)
        container.add_singleton(KasaHistoryService)
        container.add_singleton(KasaExecutionService)
        container.add_singleton(KasaRegionService)

        return container.build()


def add_container_hook(app: Quart):
    def inject_container():
        RequestContextProvider.initialize_provider(
            app=app)

        container: Container = ContainerProvider.get_container()
        container.create_scope()

        if request.view_args != None:
            request.view_args['container'] = container

    def dispose_scope(response):
        container: Container = ContainerProvider.get_container()
        container.dispose_scope()
        return response

    app.before_request_funcs.setdefault(
        None, []).append(
            inject_container)

    app.after_request_funcs.setdefault(
        None, []).append(dispose_scope)
