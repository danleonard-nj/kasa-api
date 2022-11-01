from functools import wraps
from typing import List

from framework.auth.wrappers.azure_ad_wrappers import azure_ad_authorization
from framework.dependency_injection.provider import inject_container_async
from framework.handlers.response_handler_async import response_handler
from quart import Blueprint


class MetaBlueprint(Blueprint):
    def configure(self,  rule: str, methods: List[str], auth_scheme: str):
        def decorator(function):
            @self.route(rule, methods=methods, endpoint=f'__route__{function.__name__}')
            @response_handler
            @azure_ad_authorization(scheme=auth_scheme)
            @inject_container_async
            @wraps(function)
            async def wrapper(*args, **kwargs):
                return await function(*args, **kwargs)
            return wrapper
        return decorator
