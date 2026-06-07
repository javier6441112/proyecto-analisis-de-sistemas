from sqlalchemy import func

from ..extensions import db
from ..models import MonthlyConsumption


class ConsumptionRepository:
    def average_liters_for_house(self, house_id):
        return db.session.query(func.avg(MonthlyConsumption.liters)).filter(
            MonthlyConsumption.house_id == house_id
        ).scalar()

    def average_liters(self):
        return db.session.query(func.avg(MonthlyConsumption.liters)).scalar()

    def total_liters(self):
        return db.session.query(func.coalesce(func.sum(MonthlyConsumption.liters), 0)).scalar()

    def list(self, house_id=None):
        query = MonthlyConsumption.query
        if house_id:
            query = query.filter_by(house_id=house_id)
        return query.order_by(MonthlyConsumption.period.desc()).all()

