import flask

from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask import request, jsonify

from src.app.core import models
from src.app.infrastructure import database as db
from src.app.infrastructure import ai_repository as ai_repo
from pydantic import ValidationError

bp = flask.Blueprint('ai', __name__)


@bp.route("/gen_title/", methods=["POST"])
@jwt_required()
def gen_title():
    try:
        # Модификация: добавляем force=True и проверяем тип данных
        data = flask.request.get_json(force=True, silent=True)
        if data is None:
            # Если не удалось распарсить JSON, попробуем получить данные из form-data
            description = flask.request.form.get("description")
            if description is None:
                return flask.jsonify({"error": "you must provide description to make a title"}), 400
        else:
            description = data.get("description")
        if not description:
                return flask.jsonify({"error": "you must provide description to make a title"}), 400

        return flask.jsonify({"title": ai_repo.gen_title_by_description(description)})
    except Exception as err:
        return flask.jsonify({"org": str(err), "error": "ProxyAPI or OpenAPI services probably under maintenance or my credit balance is insufficient. Please, contact me and i'll fix it as fast as possible."}), 502

@bp.route("/enchant_description/", methods=["POST"])
@jwt_required()
def enchant_description():
    try:
        # Модификация: добавляем force=True и проверяем тип данных
        data = flask.request.get_json(force=True, silent=True)
        if data is None:
            # Если не удалось распарсить JSON, попробуем получить данные из form-data
            description = flask.request.form.get("description")
            if description is None:
                return flask.jsonify({"error": "you must provide description to do enchant"}), 400
        else:
            description = data.get("description")
        if not description:
            return flask.jsonify({"error": "you must provide description to do enchant"})

        return flask.jsonify({"description": ai_repo.enchant_text(description)})
    except Exception:
        return flask.jsonify({"error": "ProxyAPI or OpenAPI services probably under maintenance or balance is out"})