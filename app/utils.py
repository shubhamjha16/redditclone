from app import db
from app.models import Post, Comment, Vote, College, Report, ReportStatus, Notification # Import Notification
from sqlalchemy import func

def get_target_score(target_model_name, target_id):
    """
    Helper function to get the score for a post or comment.
    target_model_name should be 'Post' or 'Comment'.
    """
    score = 0
    if target_model_name == 'Post':
        score = db.session.query(func.sum(Vote.vote_type)).filter(Vote.post_id == target_id).scalar()
    elif target_model_name == 'Comment':
        score = db.session.query(func.sum(Vote.vote_type)).filter(Vote.comment_id == target_id).scalar()
    return score or 0

def get_colleges_for_navbar():
    """Returns a list of all colleges, e.g., for a navbar dropdown."""
    return College.query.order_by(College.name).all()

def get_pending_reports_count():
    """Returns the count of reports with 'pending' status."""
    return Report.query.filter_by(status=ReportStatus.PENDING).count()

def send_notification(user_id, name, payload_dict):
    """
    Creates and saves a new notification.
    :param user_id: ID of the user to notify.
    :param name: Name/type of the notification (e.g., 'new_comment').
    :param payload_dict: Dictionary containing notification-specific data.
    """
    from app.models import Notification # Import here to avoid circular imports at startup
    from app import db # Import db instance
    import json

    notification = Notification(
        user_id=user_id,
        name=name,
        payload_json=json.dumps(payload_dict)
    )
    db.session.add(notification)
    # db.session.commit() # Commit will be handled by the calling route's commit, or a background task
    # For now, let's assume the caller handles the commit. If not, uncommenting is an option.
    return notification

def get_unread_notifications_count():
    """Returns the count of unread notifications for the current user."""
    from flask_login import current_user
    if current_user.is_authenticated:
        return Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return 0
