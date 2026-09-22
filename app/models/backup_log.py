from datetime import datetime

from app import db


class BackupLog(db.Model):
    __tablename__ = "backup_logs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    backup_type = db.Column(
        db.Enum(
            "DATABASE",
            "FILES",
            name="backup_type"
        ),
        nullable=False
    )

    status = db.Column(
        db.Enum(
            "SUCCESS",
            "FAILED",
            name="backup_status"
        ),
        nullable=False
    )

    location = db.Column(
        db.String(500),
        nullable=True
    )

    size_mb = db.Column(
        db.Float,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
