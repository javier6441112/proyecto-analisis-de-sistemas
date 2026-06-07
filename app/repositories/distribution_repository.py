from ..models import DistributionPlan


class DistributionPlanRepository:
    def list_recent(self, limit=None):
        query = DistributionPlan.query.order_by(DistributionPlan.service_date.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

    def find_overlap(self, service_date, start_time, end_time):
        return DistributionPlan.query.filter(
            DistributionPlan.service_date == service_date,
            DistributionPlan.start_time < end_time,
            DistributionPlan.end_time > start_time,
        ).first()

