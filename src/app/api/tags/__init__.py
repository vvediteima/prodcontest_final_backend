import flask
from src.app.infrastructure import database as db

bp = flask.Blueprint('tags', __name__)

@bp.route('/', methods=['GET'])
def tes_index():
    tags = [
        "backend",
        "frontend",
        "mobile",
        "resume",
        "HR",
        "devops",
        "QA",
        "design",
        "marketing"
    ]

    return flask.jsonify(tags)

@bp.route("/mentors/", methods=["POST"])
def get_mentors_by_tag():
    tags = flask.request.get_json()
    if type(tags) is not list:
        return flask.Response(status=400)

    session = next(db.session_factory())
    from sqlalchemy import func, select

    # Создаём подзапрос для подсчёта совпадающих тегов
    tag_subq = select(func.unnest(db.User.tags).label("tag")).subquery()

    match_count_subq = (
        select(func.count())
        .select_from(tag_subq)
        .where(tag_subq.c.tag.in_(tags))
        .correlate(db.User)
        .scalar_subquery()
    )

    query = (
        session.query(db.User, match_count_subq.label("match_count"))
        .filter(db.User.tags.op("&&")(tags))
        .order_by(match_count_subq.desc())
    )

    all_mentors = query.all()

    all_mentors.sort(key=lambda x: x[0].rating)

    result = list()
    for raw_user in all_mentors:
        user = raw_user[0]
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
            "is_verified": user.is_verified,
            "rating": user.rating
        })

    response = flask.make_response(flask.jsonify(result))
    response.headers["X-Total-Count"] = len(result)

    return response