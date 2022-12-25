from framework.configuration import Configuration

from services.kasa_client_response_service import KasaClientResponseService


class KasaSyncService:
    def __init__(
        self,
        configuration: Configuration,
        client_response_service: KasaClientResponseService
    ):
        self.__configuration = configuration
        self.__client_response_service = client_response_service
