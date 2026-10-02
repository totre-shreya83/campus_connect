from app import db
from app.models.notification import Notification
from app.models.user import User
from app.services.mail_service import send_notification_email


def create_notification(user_id, message, type=None):
    """
    Create an in-app notification and optionally send the same
    notification by email when the user has opted in.
    """

    notification = Notification(
        user_id=user_id,
        message=message,
        type=type
    )

    db.session.add(notification)

    user = User.query.get(user_id)

    if user and user.email_notifications:
        send_notification_email(
            user,
            message
        )

    return notification


def get_unread_count(user_id):
    return Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).count()
