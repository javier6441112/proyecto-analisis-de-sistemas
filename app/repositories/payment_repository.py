from sqlalchemy import func

from ..extensions import db
from ..models import Payment


class PaymentRepository:
    def list_ordered(self):
        return Payment.query.order_by(Payment.period.desc()).all()

    def total_amount(self):
        return db.session.query(func.coalesce(func.sum(Payment.amount), 0)).scalar()

    def paid_count_for_periods(self, house_id, periods):
        return Payment.query.filter(
            Payment.house_id == house_id,
            Payment.period.in_(periods),
            Payment.paid.is_(True),
        ).count()

