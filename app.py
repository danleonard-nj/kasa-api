from dotenv import load_dotenv
from framework.abstractions.abstract_request import RequestContextProvider
from framework.serialization.serializer import configure_serializer
from framework.swagger.quart.swagger import Swagger
from quart import Quart

from routes.devices import devices_bp
from routes.health import health_bp
from routes.preset import preset_bp
from routes.region import region_bp
from routes.scene import scene_bp
from routes.events import events_bp
from utils.provider import ContainerProvider
from framework.dependency_injection.provider import InternalProvider

load_dotenv()
app = Quart(__name__)


app.register_blueprint(health_bp)
app.register_blueprint(devices_bp)
app.register_blueprint(scene_bp)
app.register_blueprint(preset_bp)
app.register_blueprint(region_bp)
app.register_blueprint(events_bp)


@app.before_serving
async def startup():
    RequestContextProvider.initialize_provider(
        app=app)


swag = Swagger(
    app=app,
    title='kasa-api')
swag.configure()

ContainerProvider.initialize_provider()
InternalProvider.bind(ContainerProvider.get_service_provider())


configure_serializer(app)


if __name__ == '__main__':
    app.run(debug=True, port='5091')
