from app import db
from app.models.notification import Notification


def create_notification(user_id, message, type=None):
    """Reusable helper for creating an in-app notification."""
    notification = Notification(
        user_id=user_id,
        message=message,
        type=type
    )
    db.session.add(notification)
    return notification


def get_unread_count(user_id):
    return Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).count()
