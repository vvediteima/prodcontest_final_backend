import flask
import logging
from flasgger import Swagger

from flask import Flask, jsonify, request
from flask_uuid import FlaskUUID
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.routing import BaseConverter
# from flask_cors import CORS

from datetime import timedelta

app = flask.Flask(__name__)
app.logger.setLevel(logging.DEBUG)
app.config['SWAGGER'] = {
    'uiversion': 3,
    # При использовании DispatcherMiddleware базовый путь для документации будет относительным к монтированию
    'specs_route': '/docs/'
}

# Включаем CORS с поддержкой всех заголовков
# app.config['CORS_HEADERS'] = 'Content-Type'
# cors = CORS(app, resources={r"/*": {"origins": "*"}})

swagger = Swagger(app, template_file='openapi.yaml')  # если swagger.yml лежит в корне проекта

class BooleanConverter(BaseConverter):
    # This regex matches the strings 'true' or 'false'
    regex = 'true|false'

    def to_python(self, value):
        # Convert the matched string into a Python boolean
        return value == 'true'

    def to_url(self, value):
        # Convert a Python boolean back into a string for the URL
        return 'true' if value else 'false'

app.config["JWT_SECRET_KEY"] = "your-secret-key"
app.url_map.converters['bool'] = BooleanConverter
jwt = JWTManager(app)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(weeks=1)

uuid_app = FlaskUUID(app)

from .test_route import bp as test_bp
app.register_blueprint(test_bp, url_prefix='/test')

from .question_route import bp as question_bp
app.register_blueprint(question_bp, url_prefix='/question')

from .auth_route import bp as reg_bp
app.register_blueprint(reg_bp, url_prefix='/auth')

from .tags import bp as tags_bp
app.register_blueprint(tags_bp, url_prefix='/tags')

from .admin_route import bp as admin_bp
app.register_blueprint(admin_bp, url_prefix='/admin')

from .request_route import bp as request_bp
app.register_blueprint(request_bp, url_prefix="/request")

from .ai_route import bp as ai_bp
app.register_blueprint(ai_bp, url_prefix="/ai")

from .user_route import bp as user_bp
app.register_blueprint(user_bp, url_prefix="/user")