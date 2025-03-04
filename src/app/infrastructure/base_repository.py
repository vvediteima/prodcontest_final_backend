from .database import session_factory
from src.app.core import models
from src.app.infrastructure import database as db

def test():
    with session_factory() as session:
        # Test your connection or logic here
        pass

def add_question_from_model(session, model: models.QuestionModel):
    session.add(db.Question(
        title=model.title,
        description=model.description,
        tags=model.tags,
        owner_id=model.owner_id,
        owner_name=model.owner_name,
        owner_surname=model.owner_surname,
        owner_login=model.owner_login
    ))


def register_user_from_model(session, model: models.UserModel):
    user = db.User(
        name=model.name,
        surname=model.surname,
        password=model.password,
        login=model.login,  # Используем логин из модели
        tags=model.tags,
        description=model.description,
        job=model.job,
        company=model.company
    )
    session.add(user)
    session.commit()
    return user  # Возвращаем объект пользователя