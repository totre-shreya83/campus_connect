from datetime import datetime

from app import db


class Download(db.Model):
    __tablename__ = "downloads"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    note_id = db.Column(
        db.Integer,
        db.ForeignKey("notes.id"),
        nullable=False,
        index=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    downloaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
