from domain.kasa.auth import AuthPolicy
from domain.rest import (CreateSceneCategoryRequest, CreateSceneRequest,
                         RunSceneRequest, UpdateSceneRequest)
from framework.logger.providers import get_logger
from framework.validators.nulls import none_or_whitespace
from quart import request
from services.kasa_scene_category_service import KasaSceneCategoryService
from services.kasa_scene_service import KasaSceneService
from utils.meta import MetaBlueprint

logger = get_logger(__name__)
scene_bp = MetaBlueprint('scene_bp', __name__)


@scene_bp.configure('/api/scene/<id>', methods=['GET'], auth_scheme=AuthPolicy.Read)
async def get_scene(container, id):
    kasa_scene_service: KasaSceneService = container.resolve(
        KasaSceneService)

    return await kasa_scene_service.get_scene(
        scene_id=id)


@scene_bp.configure('/api/scene/<id>', methods=['DELETE'], auth_scheme=AuthPolicy.Write)
async def delete_scene(container, id: str):
    kasa_scene_service = container.resolve(KasaSceneService)

    return await kasa_scene_service.delete_scene(
        scene_id=id)


@scene_bp.configure('/api/scene', methods=['GET'], auth_scheme=AuthPolicy.Read)
async def get_scenes(container):
    kasa_scene_service: KasaSceneService = container.resolve(
        KasaSceneService)

    category = request.args.get('category')

    # TODO: Move to service
    if not none_or_whitespace(category):
        return await kasa_scene_service.get_scenes_by_category(category)
    else:
        return await kasa_scene_service.get_all_scenes()


@scene_bp.configure('/api/scene', methods=['POST'], auth_scheme=AuthPolicy.Write)
async def create_scene(container):
    kasa_scene_service: KasaSceneService = container.resolve(
        KasaSceneService)

    # TODO: Move to provider, use new framework exceptions
    body = await request.get_json()
    if body is None:
        raise Exception('No request body')

    scene_request = CreateSceneRequest(
        data=body)

    return await kasa_scene_service.create_scene(
        request=scene_request)


@scene_bp.configure('/api/scene', methods=['PUT'], auth_scheme=AuthPolicy.Write)
async def update_scene(container):
    kasa_scene_service: KasaSceneService = container.resolve(
        KasaSceneService)

    body = await request.get_json()
    update_request = UpdateSceneRequest(
        data=body)

    return await kasa_scene_service.update_scene(
        update_request=update_request)


@scene_bp.configure('/api/scene/<id>/run', methods=['POST'], auth_scheme=AuthPolicy.Execute)
async def run_scene(container, id: str):
    kasa_scene_service: KasaSceneService = container.resolve(
        KasaSceneService)

    region = request.args.get('region')

    run_scene_request = RunSceneRequest(
        scene_id=id,
        region_id=region)

    result = await kasa_scene_service.run_scene(
        request=run_scene_request)

    return result


@scene_bp.configure('/api/scene/category', methods=['GET'], auth_scheme=AuthPolicy.Read)
async def get_categories(container):
    kasa_scene_cageory_service: KasaSceneCategoryService = container.resolve(
        KasaSceneCategoryService)

    return await kasa_scene_cageory_service.get_scene_categories()


@scene_bp.configure('/api/scene/category', methods=['POST'], auth_scheme=AuthPolicy.Write)
async def create_category(container):
    kasa_scene_cageory_service: KasaSceneCategoryService = container.resolve(
        KasaSceneCategoryService)

    body = await request.get_json()
    create_category = CreateSceneCategoryRequest(
        data=body)

    return await kasa_scene_cageory_service.create_scene_category(
        request=create_category)


@scene_bp.configure('/api/scene/category/<id>', methods=['DELETE'], auth_scheme=AuthPolicy.Write)
async def delete_category(container, id: str):
    kasa_scene_cageory_service: KasaSceneCategoryService = container.resolve(
        KasaSceneCategoryService)

    return await kasa_scene_cageory_service.delete_scene_category(
        scene_category_id=id)
