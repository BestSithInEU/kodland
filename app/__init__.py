import json

from flask import Flask
from flask_login import LoginManager

from app.config import Config
from app.models import Question, User, db
from app.routes import init_routes

app = Flask(__name__, template_folder="../templates")
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


init_routes(app, db, login_manager)


def add_initial_questions():
    if Question.query.first() is None:
        with open("initial_questions.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            questions = [
                Question(
                    content=q["content"],
                    topic=q["topic"],
                    answer=q["answer"],
                    q_type=q["q_type"],
                    options=q.get("options", ""),
                    points=q["points"],
                )
                for q in data["questions"]
            ]
            db.session.bulk_save_objects(questions)
            db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        add_initial_questions()
    app.run(debug=True)
