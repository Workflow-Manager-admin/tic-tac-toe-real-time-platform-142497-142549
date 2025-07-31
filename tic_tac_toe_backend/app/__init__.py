from flask import Flask
from flask_cors import CORS
from .routes.health import blp as health_blp
from .routes.auth import blp as auth_blp
from .routes.game import blp as game_blp
from .routes.profile import blp as profile_blp
from flask_smorest import Api

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app, resources={r"/*": {"origins": "*"}})
app.config["API_TITLE"] = "My Flask API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config['OPENAPI_URL_PREFIX'] = '/docs'
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

api = Api(app)
api.register_blueprint(health_blp)
api.register_blueprint(auth_blp)
api.register_blueprint(game_blp)
api.register_blueprint(profile_blp)
