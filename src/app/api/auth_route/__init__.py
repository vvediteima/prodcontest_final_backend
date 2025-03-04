import flask
import uuid
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask import request, jsonify

from src.app.core import models
from src.app.infrastructure import database as db
from pydantic import ValidationError

bp = flask.Blueprint('auth', __name__)

@bp.route('/login/', methods=['POST'])
def authorization():
    try:
        request = models.LoginRequestModel(**flask.request.get_json())
    except ValidationError as er:
        return jsonify({"error": er.errors()}), 400

    session = next(db.session_factory())

    # TODO: MAKE HASH
    try:
        user = session.query(db.User).filter(db.User.login == request.login, db.User.password == request.password).one()
    except db.sql.exc.NoResultFound:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"status": "ok", "token": create_access_token(identity=str(user.id))}), 200


@bp.route("/reg/", methods=["POST"])
def register():
    try:
        data = flask.request.get_json()
        if data is None:
            return Exception("Incorrect data")
        request = models.RegisterRequestModel(**data)
    except ValidationError as er:
        return jsonify({"error": er.errors()}), 400

    session = next(db.session_factory())

    user = db.User(**request.model_dump())

    try:
        user_model = db.User(**request.model_dump())
        session.add(user_model)
        session.commit()
    except db.sql.exc.IntegrityError:
        return jsonify({"error": "already exists"}), 409

    return jsonify({"status": "ok", "token": create_access_token(identity=str(user_model.id))})


@bp.route("/", methods=["PATCH"])
@jwt_required()
def patch_user():
    try:
        session = next(db.session_factory())
        user = session.query(db.User).filter(db.User.id == uuid.UUID(get_jwt_identity())).one()
    except Exception:
        return jsonify({"error": "User not found"}), 401

    body = flask.request.get_json()

    user.name = body.get("name", user.name)
    user.surname = body.get("surname", user.surname)
    user.password = body.get("password", user.password)
    user.description = body.get("description", user.description)
    user.job = body.get("job", user.job)
    user.company = body.get("company", user.company)
    user.tags = body.get("tags", user.tags)

    session.commit()

    return flask.jsonify({"status": "ok"}), 200