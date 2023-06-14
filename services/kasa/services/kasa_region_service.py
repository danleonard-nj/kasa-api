from typing import List

from framework.logger.providers import get_logger
from framework.validators.nulls import none_or_whitespace

from data.repositories.kasa_region_repository import KasaRegionRepository
from domain.common import KasaRegion
from domain.exceptions import (InvalidRegionException,
                               InvalidRegionIdException, RegionExistsException,
                               RegionNotFoundException)
from domain.rest import CreateRegionRequest

logger = get_logger(__name__)


class KasaRegionService:
    def __init__(
        self,
        repository: KasaRegionRepository
    ):
        self.__repository = repository

    async def get_regions(
        self,
    ) -> List[KasaRegion]:

        logger.info(f'Fetching all regions')
        regions = await self.__repository.get_all()

        models = [
            KasaRegion(data=region)
            for region in regions
        ]

        return models

    async def get_region(
        self,
        region_id: str
    ) -> KasaRegion:

        logger.info(f'Get region: {region_id}')
        if none_or_whitespace(region_id):
            raise InvalidRegionIdException(region_id)

        result = await self.__repository.get({
            'region_id': region_id
        })

        if result is None:
            raise RegionNotFoundException(region_id)

        region = KasaRegion(result)

        return region

    async def delete_region(
        self,
        region_id: str
    ):

        logger.info(f'Attempting delete for region: {region_id}')
        existing = await self.__repository.get({
            'region_id': region_id
        })

        # Throw if region doesn't exist
        if existing is None:
            raise RegionNotFoundException(region_id)

        deleted = await self.__repository.delete({
            'region_id': region_id
        })

        logger.info(f'Delete result: {deleted}')

    async def create_region(
        self,
        create_request: CreateRegionRequest
    ) -> KasaRegion:

        logger.info(f'Create regions: {create_request.region_name}')
        existing = await self.__repository.get({
            'region_name': create_request.region_name
        })

        if existing is not None:
            raise RegionExistsException(create_request.region_name)

        # Validate region name and description values
        if none_or_whitespace(create_request.region_name):
            raise InvalidRegionException('Region name is required')
        if none_or_whitespace(create_request.region_description):
            raise InvalidRegionException('Region description is required')

        # Create new region model from request
        region = KasaRegion.create_region(
            region_name=create_request.region_name,
            region_description=create_request.region_description)

        result = await self.__repository.insert(
            document=region.to_dict())

        logger.info(f'Created model: {result.inserted_id}')
        return region
