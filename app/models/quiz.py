from datetime import datetime

from app import db


class Quiz(db.Model):
    __tablename__ = "quizzes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    questions = db.relationship(
        "QuizQuestion",
        backref="quiz",
        lazy=True
    )

    attempts = db.relationship(
        "QuizAttempt",
        backref="quiz",
        lazy=True
    )


class QuizQuestion(db.Model):
    __tablename__ = "quiz_questions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    quiz_id = db.Column(
        db.Integer,
        db.ForeignKey("quizzes.id"),
        nullable=False,
        index=True
    )

    question_text = db.Column(
        db.Text,
        nullable=False
    )

    marks = db.Column(
        db.Integer,
        default=1
    )

    options = db.relationship(
        "QuizOption",
        backref="question",
        lazy=True
    )


class QuizOption(db.Model):
    __tablename__ = "quiz_options"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    question_id = db.Column(
        db.Integer,
        db.ForeignKey("quiz_questions.id"),
        nullable=False,
        index=True
    )

    option_text = db.Column(
        db.String(255),
        nullable=False
    )

    is_correct = db.Column(
        db.Boolean,
        default=False
    )


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    quiz_id = db.Column(
        db.Integer,
        db.ForeignKey("quizzes.id"),
        nullable=False,
        index=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    score = db.Column(
        db.Integer,
        default=0
    )

    attempted_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    answers = db.relationship(
        "QuizAnswer",
        backref="attempt",
        lazy=True
    )


class QuizAnswer(db.Model):
    __tablename__ = "quiz_answers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    attempt_id = db.Column(
        db.Integer,
        db.ForeignKey("quiz_attempts.id"),
        nullable=False,
        index=True
    )

    question_id = db.Column(
        db.Integer,
        db.ForeignKey("quiz_questions.id"),
        nullable=False
    )

    selected_option_id = db.Column(
        db.Integer,
        db.ForeignKey("quiz_options.id"),
        nullable=True
    )
