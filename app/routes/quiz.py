from flask import (
    Blueprint,
    render_template,
    redirect,
    request,
    url_for,
    flash,
    session,
    abort,
)
from flask_login import login_required, current_user
from app import db
from app.models.quiz import (
    Quiz,
    QuizQuestion,
    QuizAttempt,
    QuizAnswer,
)
from app.forms.quiz_forms import StartQuizForm
from app.services.quiz_service import (
    get_random_questions,
    score_attempt,
    get_leaderboard,
)

quiz_bp = Blueprint("quiz", __name__, url_prefix="/quiz")


@quiz_bp.route("/")
@login_required
def hub():
    quizzes = Quiz.query.order_by(Quiz.created_at.desc()).all()
    form = StartQuizForm()
    return render_template(
        "quiz/hub.html",
        quizzes=quizzes,
        form=form,
    )


@quiz_bp.route("/<int:quiz_id>/start", methods=["POST"])
@login_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    form = StartQuizForm()

    if not form.validate_on_submit():
        flash("Please select a valid number of questions.", "danger")
        return redirect(url_for("quiz.hub"))

    question_ids = get_random_questions(
        quiz.id,
        form.num_questions.data,
    )

    if len(question_ids) < form.num_questions.data:
        flash(
            f"Only {len(question_ids)} questions are available.",
            "warning",
        )
        return redirect(url_for("quiz.hub"))

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
    )

    db.session.add(attempt)
    db.session.commit()

    session[f"quiz_{attempt.id}_questions"] = question_ids

    return redirect(
        url_for(
            "quiz.attempt",
            quiz_id=quiz.id,
            attempt_id=attempt.id,
        )
    )


@quiz_bp.route(
    "/<int:quiz_id>/attempt/<int:attempt_id>",
    methods=["GET", "POST"],
)
@login_required
def attempt(quiz_id, attempt_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    attempt = QuizAttempt.query.get_or_404(attempt_id)

    if attempt.user_id != current_user.id:
        abort(403)

    if attempt.quiz_id != quiz.id:
        abort(404)

    question_ids = session.get(
        f"quiz_{attempt.id}_questions",
        [],
    )

    if not question_ids:
        flash("This quiz attempt is no longer active.", "warning")
        return redirect(url_for("quiz.hub"))

    questions = QuizQuestion.query.filter(
        QuizQuestion.id.in_(question_ids)
    ).all()

    question_map = {q.id: q for q in questions}
    questions = [
        question_map[qid]
        for qid in question_ids
        if qid in question_map
    ]

    if request.method == "POST":
        submitted_answers = {}

        for question in questions:
            selected = request.form.get(
                f"question_{question.id}"
            )

            if selected:
                submitted_answers[question.id] = int(selected)

        score_attempt(
            attempt,
            submitted_answers,
        )

        db.session.commit()

        session.pop(
            f"quiz_{attempt.id}_questions",
            None,
        )

        return redirect(
            url_for(
                "quiz.result",
                attempt_id=attempt.id,
            )
        )

    return render_template(
        "quiz/attempt.html",
        quiz=quiz,
        attempt=attempt,
        questions=questions,
    )


@quiz_bp.route("/result/<int:attempt_id>")
@login_required
def result(attempt_id):
    attempt = QuizAttempt.query.get_or_404(attempt_id)

    if (
        attempt.user_id != current_user.id
        and not current_user.is_admin()
    ):
        abort(403)

    quiz = Quiz.query.get_or_404(attempt.quiz_id)

    total_possible = sum(QuizQuestion.query.get(answer.question_id).marks for answer in attempt.answers)

    return render_template(
        "quiz/result.html",
        attempt=attempt,
        quiz=quiz,
        total_possible=total_possible,
    )


@quiz_bp.route("/history")
@login_required
def history():
    attempts = (
        QuizAttempt.query
        .filter_by(user_id=current_user.id)
        .order_by(QuizAttempt.attempted_at.desc())
        .all()
    )

    return render_template(
        "quiz/history.html",
        attempts=attempts,
    )


@quiz_bp.route("/<int:quiz_id>/leaderboard")
@login_required
def leaderboard(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    leaderboard_data = get_leaderboard(
        quiz.id,
        limit=10,
    )

    return render_template(
        "quiz/leaderboard.html",
        quiz=quiz,
        leaderboard=leaderboard_data,
    )




