import flask
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity


bp = flask.Blueprint('test', __name__)

@bp.route('/', methods=['GET'])
def tes_index():
    return "abobus"


@bp.route("/get_jwt", methods=["GET"])
def tes_get_jwt():
    access_token = create_access_token(identity="abobus")
    return flask.jsonify(access_token=access_token)

@bp.route("/test_jwt", methods=["GET"])
@jwt_required()
def tes_test_jwt():
    access_token = create_access_token(identity="abobus")
    return flask.jsonify(token=access_token)