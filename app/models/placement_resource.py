from datetime import datetime

from app import db


class PlacementResource(db.Model):
    __tablename__ = "placement_resources"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    section = db.Column(
        db.Enum(
            "APTITUDE",
            "CODING",
            "INTERVIEW",
            "HR",
            "RESUME",
            "MATERIALS",
            name="placement_section"
        ),
        nullable=False,
        index=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=True
    )

    s3_key = db.Column(
        db.String(500),
        nullable=True
    )

    external_link = db.Column(
        db.String(500),
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
