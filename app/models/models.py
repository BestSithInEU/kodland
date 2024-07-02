from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    answer = db.Column(db.String(50), nullable=False)
    q_type = db.Column(db.String(50), nullable=False)
    options = db.Column(db.String(200))
    points = db.Column(db.Integer, default=1)


class UserScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("scores", lazy=True))
    high_score = db.Column(db.Float, nullable=False)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
