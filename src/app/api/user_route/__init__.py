import flask
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.app.infrastructure import database as db

bp = flask.Blueprint('user', __name__)

@bp.route("/info/me/", methods=["GET"])
@jwt_required()
def get_info_about_me():
    session = next(db.session_factory())
    user_id = get_jwt_identity()
    if user_id is None:
        return flask.jsonify({"error": "something wrong with your authorization token. Please, renew it"}), 400
    try:
        user = session.query(db.User).filter(db.User.id == user_id).first()
        if not user:
            return flask.jsonify({"error": "User not found"}), 404


        return flask.jsonify(user.to_dict()), 200

    except Exception as e:
        session.rollback()
        return flask.jsonify({"error": str(e)}), 500

    finally:
        session.close()