from app import db
from app.models.contribution import Contribution
from app.models.user import User

POINTS = {
    "note_approved": 10,
    "helpful_reply": 5,
    "popular_contribution": 20,
}


def award_points(user_id, reason, reference_id=None):
    """Awards points and logs the contribution. Caller commits."""
    points = POINTS.get(reason, 0)

    if points == 0:
        return None

    db.session.add(
        Contribution(
            user_id=user_id,
            points=points,
            reason=reason,
            reference_id=reference_id,
        )
    )

    user = User.query.get(user_id)

    if user:
        user.points = (user.points or 0) + points

    return points


def get_contributor_leaderboard(limit=20):
    return (
        User.query
        .filter(User.points > 0)
        .order_by(User.points.desc())
        .limit(limit)
        .all()
    )
