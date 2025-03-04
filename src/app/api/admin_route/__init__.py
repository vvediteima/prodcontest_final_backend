import datetime
import flask
from flask import request, jsonify
from sqlalchemy import func
from sqlalchemy.exc import NoResultFound
from src.app.infrastructure import database as db
from src.app.infrastructure import base_repository  # Если потребуется
from src.app.infrastructure.database import session_factory, User, Question

bp = flask.Blueprint('admin_route', __name__)


@bp.route('/stats/', methods=['GET'])
def get_stats():
    """
    Эндпоинт для получения статистики.
    Возвращает:
      - Общее количество пользователей.
      - Общее количество вопросов.
      - Среднее количество вопросов на пользователя.
      - Максимальное и минимальное количество вопросов у одного пользователя.
    """
    session = next(session_factory())
    try:
        total_users = session.query(func.count(User.id)).scalar() or 0
        total_questions = session.query(func.count(Question.id)).scalar() or 0

        avg_questions = total_questions / total_users if total_users > 0 else 0

        # Вычисляем максимальное и минимальное число вопросов, созданных одним пользователем
        user_question_counts = (
            session.query(
                Question.owner_id,
                func.count(Question.id).label("q_count")
            )
            .group_by(Question.owner_id)
            .all()
        )

        if user_question_counts:
            max_questions = max(count for _, count in user_question_counts)
            min_questions = min(count for _, count in user_question_counts)
        else:
            max_questions = 0
            min_questions = 0

        stats = {
            "total_users": total_users,
            "total_questions": total_questions,
            "avg_questions_per_user": avg_questions,
            "max_questions_by_user": max_questions,
            "min_questions_by_user": min_questions,
        }
        return jsonify(stats), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()

@bp.route("/all_requests/", methods=["GET"])
def get_all_requests():
    session = next(db.session_factory())
    try:
        all_requests = session.query(db.Request).all()
        return [{
            "id": str(req.id),
            "owner": req.owner.to_dict(),
            "mentor": req.mentor.to_dict(),
            "question": req.question.to_dict(only=["id", "title", "description", "tags", "mentor_id", "owner_id", "status", "rating_payed"]),
            "status": req.status,
            "description": req.description
        } for req in all_requests]
    except Exception:
        return []

@bp.route('/users/', methods=['GET'])
def get_all_users():
    """
    Эндпоинт для получения всех пользователей.
    Возвращаются все поля, кроме пароля.
    """
    session = next(session_factory())
    try:
        users = session.query(User).all()
        result = []
        for user in users:
            result.append(user.to_dict(only=["id", "name", "surname", "password", "login", "tags", "description", "job", "company", "is_banned", "is_verified", "rating"]))
        return jsonify(result), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()


@bp.route('/user/block/<uuid:user_id>/', methods=['PATCH'])
def block_user(user_id):
    """
    Эндпоинт для блокировки пользователя по id.
    Поле is_banned изменяется на True.
    """
    session = next(session_factory())
    try:
        # Ищем пользователя по id
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Изменяем значение поля is_banned на True
        user.is_banned = True
        session.commit()
        return jsonify({"message": f"User {user_id} is blocked"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()

@bp.route('/user/set_verified/<uuid:user_id>/<bool:is_verified>/', methods=['PATCH'])
def change_verification(user_id, is_verified):
    """
    Эндпоинт для верификации пользователя по id.
    Поле is_verified изменяется на True.
    """
    session = next(session_factory())
    try:
        # Ищем пользователя по id
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Изменяем значение поля is_banned на True
        user.is_verified = is_verified
        session.commit()
        return jsonify({"verificated": is_verified, "message": f"User {user_id} verification status changed to {is_verified}"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()

@bp.route('/user/unblock/<uuid:user_id>/', methods=['PATCH'])
def unblock_user(user_id):
    """
    Эндпоинт для разблокировки пользователя по id.
    Поле is_banned изменяется на False.
    """
    session = next(session_factory())
    try:
        # Ищем пользователя по id
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Устанавливаем значение поля is_banned в False
        user.is_banned = False
        session.commit()
        return jsonify({"message": f"User {user_id} is unblocked"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()
