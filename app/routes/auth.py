from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)

from itsdangerous import (
    URLSafeTimedSerializer,
    SignatureExpired,
    BadSignature,
)

from app import db
from app.models.user import User
from app.forms.auth_forms import (
    RegisterForm,
    LoginForm,
    ForgotPasswordForm,
    ResetPasswordForm,
)


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _get_serializer():
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()

    if form.validate_on_submit():
        existing = User.query.filter_by(
            email=form.email.data.lower().strip()
        ).first()

        if existing:
            flash(
                "An account with this email already exists.",
                "danger"
            )
            return render_template(
                "auth/register.html",
                form=form
            )

        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
            department=(
                form.department.data.strip()
                if form.department.data
                else None
            ),
            semester=form.semester.data,
            role="STUDENT",
        )

        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash(
            "Registration successful. Please log in.",
            "success"
        )

        return redirect(url_for("auth.login"))

    return render_template(
        "auth/register.html",
        form=form
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data.lower().strip()
        ).first()

        if user and user.check_password(form.password.data):

            if not user.is_active_flag:
                flash(
                    "This account has been deactivated. Contact admin.",
                    "danger"
                )

                return render_template(
                    "auth/login.html",
                    form=form
                )

            login_user(user)

            flash(
                f"Welcome back, {user.full_name}!",
                "success"
            )

            next_page = request.args.get("next")

            return redirect(
                next_page or url_for("main.index")
            )

        flash(
            "Invalid email or password.",
            "danger"
        )

    return render_template(
        "auth/login.html",
        form=form
    )


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()

    flash(
        "You have been logged out.",
        "info"
    )

    return redirect(url_for("main.index"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data.lower().strip()
        ).first()

        if user:
            serializer = _get_serializer()

            token = serializer.dumps(
                user.email,
                salt="password-reset"
            )

            reset_url = url_for(
                "auth.reset_password",
                token=token,
                _external=True
            )

            # Development mode:
            # Directly open the password reset page.
            return redirect(reset_url)

        else:
            flash(
                "If that email is registered, "
                "a reset link has been generated.",
                "info"
            )

            return redirect(url_for("auth.login"))

    return render_template(
        "auth/forgot_password.html",
        form=form
    )

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    serializer = _get_serializer()

    try:
        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=3600
        )

    except SignatureExpired:
        flash(
            "This reset link has expired. "
            "Please request a new one.",
            "danger"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    except BadSignature:
        flash(
            "Invalid reset link.",
            "danger"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    user = User.query.filter_by(
        email=email
    ).first()

    if not user:
        flash(
            "Invalid reset link.",
            "danger"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    form = ResetPasswordForm()

    if form.validate_on_submit():
        user.set_password(
            form.password.data
        )

        db.session.commit()

        flash(
            "Password reset successful. Please log in.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/reset_password.html",
        form=form
    )


@auth_bp.route("/profile")
@login_required
def profile():
    return render_template(
        "profile.html",
        user=current_user
    )
