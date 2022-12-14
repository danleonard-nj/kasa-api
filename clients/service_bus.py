from azure.servicebus import ServiceBusMessage, TransportType
from azure.servicebus.aio import ServiceBusClient
from framework.configuration.configuration import Configuration
from framework.logger.providers import get_logger
from framework.validators.nulls import not_none

from domain.exceptions import NullArgumentException

logger = get_logger(__name__)


class EventClient:
    def __init__(
        self,
        configuration: Configuration
    ):
        connecion_string = configuration.service_bus.get(
            'connection_string')

        self.__queue_name = configuration.service_bus.get(
            'queue_name')
        self.__client = ServiceBusClient.from_connection_string(
            conn_str=connecion_string,
            logging_enable=True,
            transport_type=TransportType.Amqp)

    async def send_messages(
        self,
        messages: list[ServiceBusMessage]
    ) -> None:
        '''
        Send a batch of service bus messages
        '''

        NullArgumentException.if_none(messages, 'messages')
        logger.info(f'Getting service bus queue sender')

        # TODO: Batch the mesages batches to prevent exceeding max batch size
        batch = await self.sender.create_message_batch()
        for message in messages:
            logger.info(
                f'Adding message to batch: {message.message_id}: {message.correlation_id}')
            batch.add_message(message)

        await self.sender.send_messages(batch)
        logger.info(f'Messages sent successfully')

    async def send_message(
        self,
        message: ServiceBusMessage
    ) -> None:
        '''
        Send a service bus message
        '''

        NullArgumentException.if_none(message, 'message')
        logger.info(f'Getting service bus queue sender')

        sender = self.__client.get_queue_sender(
            queue_name=self.__queue_name)

        await sender.send_messages(
            message=message)

        logger.info(f'Message sent successfully')
