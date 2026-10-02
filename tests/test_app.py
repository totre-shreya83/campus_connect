import pytest

from app import create_app, db
from app.models.user import User


@pytest.fixture()
def app():
    app = create_app("development")

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def test_app_starts(app):
    assert app is not None
    assert app.config["SQLALCHEMY_DATABASE_URI"].startswith(
        "mysql+pymysql://"
    )


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_login_page(client):
    response = client.get("/auth/login")
    assert response.status_code == 200


def test_user_password_hashing(app):
    with app.app_context():
        user = User(
            full_name="CI Test User",
            email="ci-test@example.com",
            role="STUDENT",
        )
        user.set_password("TestPassword123!")

        db.session.add(user)
        db.session.commit()

        saved_user = User.query.filter_by(
            email="ci-test@example.com"
        ).first()

        assert saved_user is not None
        assert saved_user.check_password("TestPassword123!")
        assert not saved_user.check_password("WrongPassword123!")
