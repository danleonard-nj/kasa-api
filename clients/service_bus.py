import asyncio
from azure.servicebus import ServiceBusMessage, TransportType
from azure.servicebus.aio import ServiceBusClient
from framework.configuration.configuration import Configuration
from framework.logger.providers import get_logger
from framework.validators.nulls import not_none

logger = get_logger(__name__)


class QueueClient:
    def __init__(self, container=None):
        self.configuration = container.resolve(Configuration)
        config = self.configuration.service_bus

        self.__connection_string = config.get('connection_string')
        self.__queue_name = config.get('queue_name')

        not_none(self.__connection_string, 'connection_string')
        not_none(self.__queue_name, 'queue_name')

        self.__is_initialized = False

    async def initialize(
        self
    ):
        logger.info(f'Initializing service bus client and sender')

        client = ServiceBusClient.from_connection_string(
            conn_str=self.__connection_string,
            logging_enable=True,
            transport_type=TransportType.Amqp)

        sender = client.get_queue_sender(
            queue_name=self.__queue_name)

        self.__is_initialized = True
        self.client = client
        self.sender = sender

        logger.info(f'Client initialized successfully')

    async def get_sender(
        self
    ):
        if not self.__is_initialized:
            await self.initialize()

        return self.sender

    async def send_messages(
        self,
        messages: list[ServiceBusMessage]
    ) -> None:
        logger.info(f'Getting service bus queue sender')
        not_none(messages, 'messages')

        sender = await self.get_sender()

        batch = await sender.create_message_batch()
        for message in messages:
            logger.info(
                f'Adding message to batch: {message.message_id}: {message.correlation_id}')
            batch.add_message(message)

        await sender.send_messages(batch)
        logger.info(f'Messages sent successfully')

    async def send_message(
        self,
        message: ServiceBusMessage
    ) -> None:
        logger.info(f'Getting service bus queue sender')
        not_none(message, 'message')

        sender = await self.get_sender()

        await sender.send_messages(
            message=message)
        logger.info(f'Message sent successfully')
