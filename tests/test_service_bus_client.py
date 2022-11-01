from azure.servicebus import ServiceBusClient
import pytest
from clients.service_bus import QueueClient
from utils.helpers import TestData
from unittest.mock import (
    Mock,
    patch
)
import unittest
import json

from framework.configuration.configuration import Configuration
from framework.testing.helpers import guid
from framework.testing.mocks import MockContainer


@pytest.mark.asyncio
class ServiceBusClientTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        configuration = Mock()
        container = MockContainer()

        configuration.service_bus = {
            'queue_name': guid(),
            'connection_string': guid()
        }

        container.define(
            Configuration,
            configuration)

        self.container = container

    # @patch.object(ServiceBusClient, 'from_connection_string')
    # def test_send_message(self, mock):
    #     test_data = TestData()

    #     mock_client = Mock(name='mock-client')
    #     mock.return_value = mock_client

    #     mock_sender = Mock(name='mock-sender')
    #     mock_client.get_queue_sender.return_value = mock_sender

    #     client = QueueClient(self.container)

    #     event_message = test_data.get_event_message()

    #     client.send_message(event_message)

    #     mock_client.get_queue_sender.assert_called_once()
    #     mock_sender.send_messages.assert_called_once()

    #     _, kwargs = mock_sender.send_messages.call_args
    #     message = json.loads(str(kwargs.get('message')))

    #     self.assertIsNotNone(message)
    #     self.assertEqual(message.get('endpoint'), event_message.endpoint)
    #     self.assertEqual(message.get('method'), event_message.method)
    #     self.assertEqual(message.get('body'), event_message.body)
    #     self.assertEqual(message.get('info'), event_message.info)
