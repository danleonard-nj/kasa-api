import uuid
from datetime import datetime

from data.repositories.kasa_client_response_repository import \
    KasaClientResponseRepository
from domain.kasa.client_response import KasaClientResponse
from domain.rest import UpdateClientResponseRequest
from services.kasa_client_response_service import KasaClientResponseService
from tests.buildup import ApplicationBase
from tests.helpers import TestHelper

helper = TestHelper()


class KasaClientResponseTests(ApplicationBase):
    async def asyncSetUp(
        self
    ) -> None:
        self.repo = self.resolve(KasaClientResponseRepository)
        self.service = self.resolve(KasaClientResponseService)

    async def test_get_client_response(self):
        # Arrange
        service: KasaClientResponseService = self.resolve(
            KasaClientResponseService)
        repository: KasaClientResponseRepository = self.resolve(
            KasaClientResponseRepository)

        device_id = str(uuid.uuid4())

        record = {
            'client_response_id': str(uuid.uuid4()),
            'device_id': device_id,
            'preset_id': str(uuid.uuid4()),
            'client_response': dict(),
            'state_key': str(uuid.uuid4()),
            'created_date': datetime.now(),
            'modified_date': datetime.now()
        }

        insert_result = await repository.insert(record)

        # Act
        client_response = await service.get_client_response(
            device_id=device_id)

        # Assert
        self.assertIsNotNone(client_response)
        self.assertEqual(client_response.device_id, device_id)
        self.assertEqual(insert_result.acknowledged, True)

    async def test_create_client_response(self):
        # Arrange
        service: KasaClientResponseService = self.resolve(
            KasaClientResponseService)
        repository: KasaClientResponseRepository = self.resolve(
            KasaClientResponseRepository)

        device_id = str(uuid.uuid4())
        test_id = str(uuid.uuid4())

        await service.create_client_response(
            device_id=device_id,
            preset_id=str(uuid.uuid4()),
            client_response=dict(test=test_id),
            state_key=str(uuid.uuid4())
        )

        record = await repository.get({
            'device_id': device_id
        })

        client_response = KasaClientResponse.from_entity(
            data=record)

        # Assert
        self.assertIsNotNone(client_response)
        self.assertEqual(client_response.client_response.get('test'), test_id)
        self.assertEqual(client_response.device_id, device_id)

    async def test_update_client_response(self):
        # Arrange
        service: KasaClientResponseService = self.resolve(
            KasaClientResponseService)
        repository: KasaClientResponseRepository = self.resolve(
            KasaClientResponseRepository)

        device_id = str(uuid.uuid4())
        update_id = str(uuid.uuid4())
        updated_response = {
            'test': update_id
        }

        req = UpdateClientResponseRequest({
            'device_id': device_id,
            'preset_id': str(uuid.uuid4()),
            'client_response': updated_response,
            'state_key': str(uuid.uuid4())
        })

        existing_client_response_record = {
            'client_response_id': str(uuid.uuid4()),
            'device_id': device_id,
            'preset_id': str(uuid.uuid4()),
            'client_response': dict(),
            'state_key': str(uuid.uuid4()),
            'created_date': datetime.now(),
            'modified_date': datetime.now()
        }

        insert_result = await repository.insert(
            existing_client_response_record)

        # Act
        update_result = await service.update_client_response(
            request=req)

        updated_entity = await repository.get({
            'device_id': device_id
        })

        updated_record = KasaClientResponse.from_entity(
            data=updated_entity)
        updated_value = updated_record.client_response.get('test')

        # Assert
        self.assertIsNotNone(update_result)
        self.assertIsNotNone(updated_record)
        self.assertEqual(updated_value, update_id)
        self.assertEqual(insert_result.acknowledged, True)
