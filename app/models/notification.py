from datetime import datetime

from app import db


class Notification(db.Model):
    __tablename__ = "notifications"

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

    message = db.Column(
        db.String(255),
        nullable=False
    )

    type = db.Column(
        db.String(50),
        nullable=True
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        index=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
