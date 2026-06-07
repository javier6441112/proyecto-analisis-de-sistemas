from sqlalchemy import or_

from ..models import Notification


class NotificationRepository:
    def list_for_role(self, role, limit=None):
        query = Notification.query.order_by(Notification.created_at.desc()).filter(
            or_(Notification.recipient_role.is_(None), Notification.recipient_role == role)
        )
        if limit:
            query = query.limit(limit)
        return query.all()

    def unread_count_for_role(self, role):
        return Notification.query.filter(
            or_(Notification.recipient_role.is_(None), Notification.recipient_role == role),
            Notification.is_read.is_(False),
        ).count()

    def first(self):
        return Notification.query.first()

    def get_or_404(self, notification_id):
        return Notification.query.get_or_404(notification_id)

