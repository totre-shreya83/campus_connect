from datetime import datetime

from flask_login import UserMixin

from app import db, bcrypt, login_manager


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.Enum(
            "STUDENT",
            "ADMIN",
            name="user_role"
        ),
        default="STUDENT",
        nullable=False
    )

    department = db.Column(
        db.String(100),
        nullable=True
    )

    semester = db.Column(
        db.Integer,
        nullable=True
    )

    points = db.Column(
        db.Integer,
        default=0
    )

    is_active_flag = db.Column(
        "is_active",
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    notes = db.relationship(
        "Note",
        backref="uploader",
        lazy=True,
        foreign_keys="Note.uploader_id"
    )

    requests = db.relationship(
        "NoteRequest",
        backref="requester",
        lazy=True
    )

    def set_password(self, raw_password):
        self.password_hash = (
            bcrypt
            .generate_password_hash(raw_password)
            .decode("utf-8")
        )

    def check_password(self, raw_password):
        return bcrypt.check_password_hash(
            self.password_hash,
            raw_password
        )

    def is_admin(self):
        return self.role == "ADMIN"

    @property
    def is_active(self):
        return self.is_active_flag


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))