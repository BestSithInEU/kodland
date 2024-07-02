import re

from flask import flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import UserMixin, current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import Question, User, UserScore, db


def init_routes(app, db, login_manager):
    @app.route("/")
    def home():
        print(
            "Kullanıcının kimliği doğrulandı mı?:", current_user.is_authenticated
        )  #! Debugging
        print("Geçerli Kullanıcı:", current_user)  #! Debugging
        return render_template("main.html", current_user=current_user)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                print("Kullanıcı giriş yaptı:", current_user)  #! Debugging
                flash("Başarıyla giriş yaptınız!")
                return redirect(url_for("home"))
            else:
                flash("Kullanıcı adı veya şifre hatalı.")
                return redirect(url_for("login"))
        return render_template("login.html")

    @app.route("/questions", methods=["GET"])
    def get_questions():
        questions = Question.query.all()
        return jsonify([{"id": q.id, "content": q.content} for q in questions])

    @app.route("/add_question", methods=["GET", "POST"])
    def add_question():
        if request.method == "POST":
            content = request.form["content"]
            topic = request.form["topic"]
            answer = request.form["answer"]
            q_type = request.form["q_type"]
            options = request.form["options"] if "options" in request.form else None
            points = request.form.get("points", type=int)

            new_question = Question(
                content=content,
                topic=topic,
                answer=answer,
                q_type=q_type,
                options=options,
                points=points,
            )
            db.session.add(new_question)
            db.session.commit()
            flash("Soru başarıyla eklendi!")
            return redirect(url_for("add_question"))
        return render_template("add_question.html")

    @app.route("/remove_question", methods=["GET", "POST"])
    def remove_question():
        if request.method == "POST":
            if "questionId" not in request.form:
                flash("Soru Seçilmedi.")
                return redirect(url_for("remove_question"))

            question_id = request.form["questionId"]
            question = Question.query.get(question_id)
            if question:
                db.session.delete(question)
                db.session.commit()
                flash("Soru Başarıyla Çıkarıldı!")
            else:
                flash("Soru Bulunamadi.")
            return redirect(url_for("remove_question"))
        else:
            questions = Question.query.all()
            if not questions:
                return render_template("remove_question.html", questions=[])
            return render_template("remove_question.html", questions=questions)

    @app.route("/highscore/<int:user_id>")
    def high_score(user_id):
        score = UserScore.query.filter_by(user_id=user_id).first()
        return jsonify({"high_score": score.high_score if score else 0})

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Başarıyla çıkış yaptınız.")
        return redirect(url_for("home"))

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            existing_user = User.query.filter_by(username=username).first()

            if existing_user:
                flash(
                    "Bu kullanıcı adı zaten kullanımda. Lütfen başka bir tane deneyin."
                )
                return redirect(url_for("signup"))

            hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
            new_user = User(username=username, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            print(f"Yeni kullanıcı kayıt edildi: {username}")  #! Debugging

            new_user_score = UserScore(user_id=new_user.id, high_score=0)
            db.session.add(new_user_score)
            db.session.commit()

            flash("Kayıt başarılı! Şimdi giriş yapabilirsiniz.")
            return redirect(url_for("login"))

        return render_template("signup.html")

    @app.route("/test", methods=["GET", "POST"])
    def test():
        page = request.args.get("page", 1, type=int)
        per_page = 5

        question_query = Question.query
        total_questions = question_query.count()
        total_pages = (total_questions + per_page - 1) // per_page

        if request.method == "POST":
            page_answers = {}
            for key, value in request.form.items():
                if key.startswith("page_"):
                    page_answers[key] = value
            session[f"page_{page}_answers"] = page_answers
            session.modified = True
            print(f"Sayfa {page} cevapları:", page_answers)  #! Debugging

            if page < total_pages:
                return redirect(url_for("test", page=page + 1))
            else:
                session[f"page_{page}_answers"] = page_answers
                session.modified = True
                return redirect(url_for("submit_all"))

        saved_answers = {}
        for p in range(1, total_pages + 1):
            saved_answers.update(session.get(f"page_{p}_answers", {}))

        questions_to_display = question_query.paginate(
            page=page, per_page=per_page, error_out=False
        ).items

        best_score = 0
        if current_user.is_authenticated:
            user_score = UserScore.query.filter_by(user_id=current_user.id).first()
            if user_score:
                best_score = user_score.high_score

        return render_template(
            "test.html",
            questions=questions_to_display,
            saved_answers=saved_answers,
            page=page,
            total_pages=total_pages,
            is_last_page=(page == total_pages),
            best_score=best_score,
        )

    @app.route("/submit", methods=["GET", "POST"])
    def submit_all():
        user_id = current_user.id
        score = 0
        per_page = 5

        all_answers = {}
        total_pages = (Question.query.count() + per_page - 1) // per_page
        for page in range(1, total_pages + 1):
            page_answers = session.get(f"page_{page}_answers", {})
            print(f"Sayfa {page} cevapları:", page_answers)  #! Debugging
            all_answers.update(page_answers)

        print("Bütün cevaplar toplandı:", all_answers)  #! Debugging

        if not all_answers:
            flash("Lütfen tüm soruları cevaplayın.")
            return redirect(url_for("test", page=1))

        for question in Question.query.all():
            pattern = re.compile(rf"page_\d+_answer_{question.id}")
            answer_key = next((k for k in all_answers if pattern.match(k)), None)
            if answer_key:
                user_answer = all_answers[answer_key].strip().lower()
                correct_answer = question.answer.strip().lower()
                is_correct = user_answer == correct_answer
                print(
                    f"Soru ID: {question.id}, Kullanıcı Cevabı: {user_answer}, Doğru Cevap: {correct_answer}, Doğru mu: {'Evet' if is_correct else 'Hayır'}"
                )  #! Debugging

                if is_correct:
                    score += question.points
            else:
                print(f"Soru ID: {question.id} için cevap bulunamadı.")  #! Debugging

        print(f"Toplam puan: {score}")  #! Debugging
        # Kullanıcının puanını kaydet
        user_score = UserScore.query.filter_by(user_id=user_id).first()
        if user_score:
            if score > user_score.high_score:
                user_score.high_score = score
        else:
            user_score = UserScore(user_id=user_id, high_score=score)
        db.session.add(user_score)
        db.session.commit()

        top_scores = (
            UserScore.query.order_by(UserScore.high_score.desc()).limit(10).all()
        )
        print(
            "En yüksek puanlar:",
            [(score.user_id, score.high_score) for score in top_scores],
        )  #! Debugging

        # Session'daki cevapları temizle
        for page in range(1, total_pages + 1):
            session.pop(f"page_{page}_answers", None)

        return render_template(
            "results.html",
            score=score,
            top_scores=top_scores,
            current_user=current_user,
        )
