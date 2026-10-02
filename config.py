import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-key-not-secure"
    )

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
    BACKUP_PREFIX = os.environ.get("BACKUP_PREFIX", "backups/db/")

    SES_SENDER_EMAIL = os.environ.get(
        "SES_SENDER_EMAIL",
        "no-reply@campusconnect.example.com"
    )

    SES_ENABLED = os.environ.get(
        "SES_ENABLED",
        "false"
    ).lower() == "true"

    MAX_CONTENT_LENGTH = 20 * 1024 * 1024


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False

    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"
    REMEMBER_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}

