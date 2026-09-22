from datetime import datetime

from app import db


class NoteRequest(db.Model):
    __tablename__ = "note_requests"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    requester_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    subject = db.Column(
        db.String(100),
        index=True
    )

    semester = db.Column(
        db.Integer,
        index=True
    )

    department = db.Column(
        db.String(100),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    status = db.Column(
        db.Enum(
            "OPEN",
            "FULFILLED",
            name="request_status"
        ),
        default="OPEN",
        index=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    replies = db.relationship(
        "RequestReply",
        backref="request",
        lazy=True
    )


class RequestReply(db.Model):
    __tablename__ = "request_replies"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("note_requests.id"),
        nullable=False
    )

    responder_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    note_id = db.Column(
        db.Integer,
        db.ForeignKey("notes.id"),
        nullable=True
    )

    message = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    responder = db.relationship(
        "User",
        foreign_keys=[responder_id]
    )

