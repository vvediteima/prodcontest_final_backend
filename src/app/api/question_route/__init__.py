import flask
from sqlalchemy import func
from flask import request, jsonify
from pydantic import ValidationError
from src.app.core import models
from src.app.infrastructure import database as db
from src.app.infrastructure import base_repository as db_repo
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity

bp = flask.Blueprint('question', __name__)


@bp.route('/', methods=['POST'])
@jwt_required()
def add_question():
    try:
        request = models.QuestionModel(**flask.request.get_json())
    except ValidationError as er:
        return jsonify({"error": er.errors()}), 400

    session = next(db.session_factory())
    try:
        user = session.query(db.User).filter(db.User.id == get_jwt_identity()).one()
    except Exception:
        return flask.jsonify({"error": "something wrong with user"})

    question = db.Question(
        title=request.title,
        description=request.description,
        tags=request.tags,
        owner_id=user.id,
    )

    session.add(question)
    session.commit()
    return jsonify({"question_id": question.id, "message": "Question added successfully."}), 201


@bp.route('/<uuid:question_uuid>/', methods=['DELETE'])
@jwt_required()
def remove_question(question_uuid):
    session = next(db.session_factory())
    try:
        question = session.query(db.Question).filter(
            db.Question.id == question_uuid
        ).one()
    except Exception:
        # Если вопрос не найден, можно вернуть 404 или 204
        return jsonify({"error": "Question not found"}), 404

    if (question.status == 1):
        return jsonify({"error": "You cant delete the solved question."}), 403

    try:
        requests = session.query(db.Request).filter(db.Request.question_id == question.id).all()
        for request in requests:
            session.delete(request)
    except Exception:
        pass

    session.delete(question)
    session.commit()
    return jsonify({"message": "Question deleted successfully."}), 200


@bp.route("/<uuid:question_id>/solved/", methods=["POST"])
@jwt_required()
def question_is_solved(question_id):
    session = next(db.session_factory())
    try:
        user_id = get_jwt_identity()
        question = session.query(db.Question).filter(db.Question.id == question_id,
                                                     db.Question.owner_id == user_id).one()
        if question.mentor_id is None:
            return flask.jsonify({"error": "the request is not accepted already"}), 400

        question.status = 1
        question.mentor.rating += question.rating_payed
        session.commit()
        return flask.Response(status=201)

    except Exception as err:
        return flask.jsonify({"error": str(err)}), 400


@bp.route('/', methods=['GET'])
@jwt_required()
def get_questions():
    session = next(db.session_factory())
    try:
        user_id = get_jwt_identity()
        questions = session.query(db.Question).filter(db.Question.owner_id == user_id, db.Question.status == 0).all()
    except Exception:
        return flask.Response(status=404)

    result = [question.to_dict() for question in questions]

    return jsonify(result), 201


@bp.route('/<uuid:question_uuid>/', methods=['GET'])
@jwt_required()
def get_mentors(question_uuid):
    session = next(db.session_factory())
    try:
        # Получаем вопрос по UUID
        question = session.query(db.Question).filter(db.Question.id == question_uuid).one()
    except Exception:
        return jsonify({"error": "Question not found"}), 404

    # Формируем фильтр: преобразуем массив tags в строку и ищем подстроку для каждого тега вопроса.
    filters = [
        func.array_to_string(db.User.tags, ',').ilike(f'%{tag}%')
        for tag in question.tags
    ]
    mentors = session.query(db.User).filter(db.sql.or_(*filters), db.User.id != get_jwt_identity()).all()

    result = []
    for user in mentors:
        result.append({
            "id": str(user.id),
            "name": user.name,
            "surname": user.surname,
            "login": user.login,
            "tags": user.tags,
            "description": user.description,
            "job": user.job,
            "company": user.company,
            "is_banned": user.is_banned,
            "is_verified": user.is_verified
        })

    return jsonify(result), 200
