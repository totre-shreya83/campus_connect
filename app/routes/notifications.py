from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app import db
from app.models.notification import Notification

notifications_bp = Blueprint(
    "notifications",
    __name__,
    url_prefix="/notifications"
)

PER_PAGE = 15


@notifications_bp.route("/")
@login_required
def list_notifications():
    page = request.args.get("page", 1, type=int)

    pagination = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .paginate(
            page=page,
            per_page=PER_PAGE,
            error_out=False
        )
    )

    return render_template(
        "notifications/list.html",
        notifications=pagination.items,
        pagination=pagination
    )


@notifications_bp.route(
    "/<int:notification_id>/read",
    methods=["POST"]
)
@login_required
def mark_read(notification_id):
    notification = Notification.query.get_or_404(
        notification_id
    )

    if notification.user_id != current_user.id:
        abort(403)

    notification.is_read = True
    db.session.commit()

    next_page = request.args.get("next")

    return redirect(
        next_page
        or url_for("notifications.list_notifications")
    )


@notifications_bp.route(
    "/mark-all-read",
    methods=["POST"]
)
@login_required
def mark_all_read():
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update(
        {"is_read": True}
    )

    db.session.commit()

    flash(
        "All notifications marked as read.",
        "success"
    )

    return redirect(
        url_for("notifications.list_notifications")
    )
