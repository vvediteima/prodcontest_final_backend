import os
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy_serializer import SerializerMixin

DATABASE_URL = os.getenv("POSTGRES_LINK", "postgresql+psycopg2://prod:prod_password@localhost:5432/prod_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

import sqlalchemy as sql


class Question(Base, SerializerMixin):
    __tablename__ = 'questions'

    id = sql.Column(sql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = sql.Column(sql.String)
    description = sql.Column(sql.String)
    tags = sql.Column(sql.ARRAY(sql.String))

    mentor_id = sql.Column(sql.UUID, sql.ForeignKey("users.id"))
    mentor = sql.orm.relationship("User", foreign_keys=[mentor_id])

    owner_id = sql.Column(sql.UUID(as_uuid=True), sql.ForeignKey('users.id'))
    owner = sql.orm.relationship("User", back_populates="questions", overlaps="User,questions", foreign_keys=[owner_id])

    status = sql.Column(sql.Integer, default=0)
    rating_payed = sql.Column(sql.Integer, default=20)

    @property
    def active_requests(self):
        session = sql.orm.object_session(self)
        if session is None:
            return 0
        return session.query(sql.func.count(Request.id)).filter(
            Request.question_id == self.id, Request.status == 0
        ).scalar()

    def to_dict(self, *args, **kwargs):
        data = super().to_dict(*args, **kwargs)
        data["active_requests"] = self.active_requests  # Добавляем в JSON
        return data


class User(Base, SerializerMixin):
    __tablename__ = 'users'
    serialize_rules = ('-questions', '-password')

    id = sql.Column(sql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = sql.Column(sql.String, nullable=False)
    surname = sql.Column(sql.String, nullable=False)
    password = sql.Column(sql.String, nullable=False)
    login = sql.Column(sql.String, unique=True, nullable=False)  # Новое уникальное поле
    tags = sql.Column(sql.ARRAY(sql.String), default=list())
    description = sql.Column(sql.String, nullable=True)
    job = sql.Column(sql.String, nullable=True)
    company = sql.Column(sql.String, nullable=True)
    is_banned = sql.Column(sql.Boolean, default=False)
    is_verified = sql.Column(sql.Boolean, default=False)

    rating = sql.Column(sql.Integer, default=0)

    questions = sql.orm.relationship("Question", back_populates="owner", overlaps="User,questions",
                                     foreign_keys=[Question.owner_id])


class Request(Base, SerializerMixin):
    __tablename__ = "requests"

    id = sql.Column(sql.UUID, primary_key=True, default=uuid.uuid4)
    owner_id = sql.Column(sql.UUID, sql.ForeignKey("users.id"))
    mentor_id = sql.Column(sql.UUID, sql.ForeignKey("users.id"))
    question_id = sql.Column(sql.UUID, sql.ForeignKey("questions.id"))
    status = sql.Column(sql.Integer, default=0)
    description = sql.Column(sql.String, nullable=True)

    owner = sql.orm.relationship("User", foreign_keys=[owner_id])
    mentor = sql.orm.relationship("User", foreign_keys=[mentor_id])
    question = sql.orm.relationship("Question")


Base.metadata.create_all(engine)


def session_factory():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
