from datetime import datetime

from app import db


class Contribution(db.Model):
    __tablename__ = "contributions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    points = db.Column(
        db.Integer,
        nullable=False
    )

    reason = db.Column(
        db.String(100),
        nullable=False
    )

    reference_id = db.Column(
        db.Integer,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
