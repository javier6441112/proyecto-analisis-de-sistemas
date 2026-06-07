from ..models import MaintenanceOrder


class MaintenanceRepository:
    def list_orders(self):
        return MaintenanceOrder.query.order_by(MaintenanceOrder.order_date.desc()).all()

    def pending_count(self):
        return MaintenanceOrder.query.filter(MaintenanceOrder.status != "finalizada").count()

    def first_order(self):
        return MaintenanceOrder.query.first()

    def get_order_or_404(self, order_id):
        return MaintenanceOrder.query.get_or_404(order_id)

