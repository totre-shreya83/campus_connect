import random

from sqlalchemy import func

from app import db
from app.models.user import User
from app.models.quiz import (
    Quiz,
    QuizQuestion,
    QuizOption,
    QuizAttempt,
    QuizAnswer,
)


def get_random_questions(quiz_id, count=10):
    question_ids = [
        row[0]
        for row in db.session.query(QuizQuestion.id)
        .filter_by(quiz_id=quiz_id)
        .all()
    ]

    random.shuffle(question_ids)

    return question_ids[:count]


def score_attempt(attempt, submitted_answers):
    score = 0

    for question_id, selected_option_id in submitted_answers.items():
        question = QuizQuestion.query.get(question_id)

        if not question:
            continue

        option = QuizOption.query.get(selected_option_id)

        if not option:
            continue

        if option.question_id != question.id:
            continue

        is_correct = option.is_correct

        answer = QuizAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option_id=option.id,
        )

        db.session.add(answer)

        if is_correct:
            score += question.marks

    attempt.score = score

    return attempt


def get_leaderboard(quiz_id, limit=10):
    rows = (
        db.session.query(
            User.full_name,
            QuizAttempt.user_id,
            func.max(QuizAttempt.score).label("best_score"),
        )
        .join(User, User.id == QuizAttempt.user_id)
        .filter(QuizAttempt.quiz_id == quiz_id)
        .group_by(User.id, User.full_name, QuizAttempt.user_id)
        .order_by(func.max(QuizAttempt.score).desc())
        .limit(limit)
        .all()
    )

    return rows







