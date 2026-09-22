from datetime import datetime

from app import db


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False,
        index=True
    )

    description = db.Column(
        db.Text,
        nullable=True
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
        index=True
    )

    faculty = db.Column(
        db.String(100),
        nullable=True
    )

    keywords = db.Column(
        db.String(255),
        index=True
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=True
    )

    file_type = db.Column(
        db.String(10),
        nullable=False
    )

    file_name = db.Column(
        db.String(255),
        nullable=False
    )

    s3_key = db.Column(
        db.String(500),
        nullable=False
    )

    uploader_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    approval_status = db.Column(
        db.Enum(
            "PENDING",
            "APPROVED",
            "REJECTED",
            name="approval_status"
        ),
        default="PENDING",
        index=True
    )

    download_count = db.Column(
        db.Integer,
        default=0
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
