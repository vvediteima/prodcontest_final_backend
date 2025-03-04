import flask

from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity

from src.app.core import models
from src.app.infrastructure import database as db
from pydantic import ValidationError

bp = flask.Blueprint('request', __name__)

@bp.route('/<uuid:question_id>/<uuid:mentor_id>/', methods=['POST'])
@jwt_required()
def add_request(question_id, mentor_id):
    user_id = get_jwt_identity()
    try:
        session = next(db.session_factory())
        session.query(db.Question).filter(db.Question.id == question_id, db.Question.owner_id == user_id).one()
    except Exception as er:
        return flask.jsonify({"error": "Question is not found"}), 400

    try:
        session = next(db.session_factory())
        mentor = session.query(db.User).filter(db.User.id == mentor_id).one()
    except Exception as er:
        return flask.jsonify({"error": "mentor is not found"}), 400

    request = db.Request(question_id=question_id, owner_id=user_id, mentor_id=mentor.id, description=flask.request.get_json().get("description", None))
    session.add(request)
    session.commit()

    return flask.Response(status=201)


@bp.route('/<uuid:question_id>/many/', methods=['POST'])
@jwt_required()
def add_many_requests(question_id):
    user_id = get_jwt_identity()
    data = flask.request.get_json()
    if type(data) is not dict:
        return flask.jsonify({"error": "You must provide fields: mentors_id:list and description:str"}), 400
    mentors_id = data.get("mentors_id", list())
    description = data.get("description", None)
    try:
        session = next(db.session_factory())
        question = session.query(db.Question).filter(db.Question.id == question_id, db.Question.owner_id == user_id).one()
    except Exception as er:
        return flask.jsonify({"error": "Question is not found"}), 400

    if question.status != 0:
        return flask.jsonify({"error": "Question is not open"}), 403

    if type(mentors_id) != list:
        return flask.jsonify({"error": "You need to provide mentors_id through a list type"})

    try:
        session = next(db.session_factory())
        mentor = session.query(db.User).filter(db.User.id.in_(mentors_id)).all()

        if len(mentors_id) != len(mentor):
            raise ValueError

    except Exception as er:
        return flask.jsonify({"error": "someone or all of these mentors is not found"}), 400

    for mentor_id in mentors_id:
        request = db.Request(question_id=question_id, owner_id=question.owner_id, mentor_id=mentor_id, description=description)
        session.add(request)
    session.commit()

    return flask.jsonify({"status": "ok"}), 201

@bp.route('/incoming/', methods=['GET'])
@jwt_required()
def get_incoming_requests():
    user_id = get_jwt_identity()  # идентификатор текущего пользователя (ментора)
    session = next(db.session_factory())
    try:
        incoming_requests = session.query(db.Request).filter(db.Request.mentor_id == user_id, db.Request.status == 0).all()
    except Exception as er:
        return flask.jsonify({"error": "Ошибка при получении заявок"}), 500

    result = []

    for req in incoming_requests:
        result.append({
            "id": str(req.id),
            "owner": req.owner.to_dict(only=["id", "name", "surname", "password", "login", "tags", "description", "job", "company", "is_banned", "is_verified", "rating"]),
            "mentor": req.mentor.to_dict(only=["id", "name", "surname", "password", "login", "tags", "description", "job", "company", "is_banned", "is_verified", "rating"]),
            "question": req.question.to_dict(only=["id", "title", "description", "tags", "mentor_id", "owner_id", "status", "rating_payed"]),
            "status": req.status,
            "description": req.description
        })
    return flask.jsonify(result), 200

@bp.route('/<uuid:request_id>/accept/', methods=['PATCH'])
@jwt_required()
def accept_request(request_id):
    user_id = get_jwt_identity()  # идентификатор текущего пользователя (ментора)
    session = next(db.session_factory())
    try:
        req_obj = session.query(db.Request).filter(db.Request.id == request_id).one()
    except Exception as e:
        return flask.jsonify({"error": "Request not found"}), 400

    # Проверка, что текущий пользователь является ментором данного запроса
    if str(req_obj.mentor_id) != str(user_id):
        return flask.jsonify({"error": "You are not authorized to accept this request"}), 400

    try:
        all_requests = session.query(db.Request).filter(db.Request.question_id == req_obj.question_id).all()
        for all_req in all_requests:
            all_req.status = -1
    except Exception:
        pass

    req_obj.status = 1
    req_obj.question.mentor_id = user_id
    session.commit()
    return flask.jsonify({"message": "Request accepted successfully."}), 200


@bp.route('/<uuid:request_id>/decline/', methods=['PATCH'])
@jwt_required()
def decline_request(request_id):
    user_id = get_jwt_identity()  # идентификатор текущего пользователя (ментора)
    session = next(db.session_factory())
    try:
        req_obj = session.query(db.Request).filter(db.Request.id == request_id).one()
    except Exception as e:
        return flask.jsonify({"error": "Request not found"}), 400

    # Проверка, что текущий пользователь является ментором данного запроса
    if str(req_obj.mentor_id) != str(user_id):
        return flask.jsonify({"error": "You are not authorized to decline this request"}), 400

    req_obj.status = -1  # устанавливаем статус "decline"
    session.commit()
    return flask.jsonify({"message": "Request declined successfully."}), 200

@bp.route('/accepted/', methods=['GET'])
@jwt_required()
def get_accepted_requests():
    user_id = get_jwt_identity()  # идентификатор текущего пользователя (ментора)
    session = next(db.session_factory())
    try:
        accepted_requests = session.query(db.Request).filter(
            db.Request.mentor_id == user_id,
            db.Request.status == 1
        ).all()
    except Exception as e:
        return flask.jsonify({"error": "Ошибка при получении заявок"}), 500


    result = []

    for req in accepted_requests:
        result.append({
            "id": str(req.id),
            "owner": req.owner.to_dict(only=["id", "name", "surname", "password", "login", "tags", "description", "job", "company", "is_banned", "is_verified", "rating"]),
            "mentor": req.mentor.to_dict(only=["id", "name", "surname", "password", "login", "tags", "description", "job", "company", "is_banned", "is_verified", "rating"]),
            "question": req.question.to_dict(only=["id", "title", "description", "tags", "mentor_id", "owner_id", "status", "rating_payed"]),
            "status": req.status,
            "description": req.description
        })
    return flask.jsonify(result), 200
