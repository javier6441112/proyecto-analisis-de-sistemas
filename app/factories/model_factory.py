from datetime import date, datetime

from ..models import (
    Cistern,
    DistributionPlan,
    House,
    MaintenanceIntervention,
    MaintenanceOrder,
    MonthlyConsumption,
    Notification,
    Payment,
    Resident,
    User,
    WaterReading,
)


class ModelFactory:
    @staticmethod
    def user(data, role=None):
        user = User(
            first_name=data["firstName"].strip(),
            last_name=data["lastName"].strip(),
            address=data["address"].strip(),
            dpi=data["dpi"].strip(),
            role=role or data["role"].strip(),
        )
        user.set_password(data["password"])
        return user

    @staticmethod
    def house(data):
        return House(
            house_number=data["houseNumber"],
            owner_name=data["ownerName"],
            address=data.get("address", "Sin dirección"),
            status=data.get("status", "activa"),
        )

    @staticmethod
    def resident(data):
        is_minor = bool(data.get("isMinor", False))
        return Resident(
            house_id=int(data["houseId"]),
            first_name=data["firstName"],
            last_name=data["lastName"],
            is_minor=is_minor,
            identification=None if is_minor else data.get("identification"),
        )

    @staticmethod
    def water_reading(cistern_id, liters, source, observation=None):
        return WaterReading(
            cistern_id=cistern_id,
            liters=liters,
            source=source,
            observation=observation,
        )

    @staticmethod
    def monthly_consumption(data, is_anomalous=False):
        return MonthlyConsumption(
            house_id=int(data["houseId"]),
            period=data["period"],
            liters=float(data.get("liters", 0)),
            observation=data.get("observation"),
            is_anomalous=is_anomalous,
        )

    @staticmethod
    def payment(data):
        return Payment(
            house_id=int(data["houseId"]),
            period=data["period"],
            amount=data["amount"],
            paid=True,
            receipt_number=data.get("receiptNumber"),
        )

    @staticmethod
    def distribution_plan(data):
        return DistributionPlan(
            service_date=datetime.strptime(data["serviceDate"], "%Y-%m-%d").date(),
            start_time=datetime.strptime(data["startTime"], "%H:%M").time(),
            end_time=datetime.strptime(data["endTime"], "%H:%M").time(),
            notes=data.get("notes"),
        )

    @staticmethod
    def maintenance_order(data):
        return MaintenanceOrder(
            order_date=datetime.strptime(data.get("orderDate", date.today().isoformat()), "%Y-%m-%d").date(),
            maintenance_type=data.get("maintenanceType", "Correctivo"),
            description=data.get("description", "Sin descripción"),
            responsible=data.get("responsible", "Soporte técnico"),
            observations=data.get("observations"),
        )

    @staticmethod
    def maintenance_intervention(data):
        return MaintenanceIntervention(
            order_id=int(data["orderId"]),
            intervention_type=data.get("interventionType", "Revisión"),
            observations=data.get("observations"),
            status=data.get("status", "finalizada"),
        )

    @staticmethod
    def notification(title, message, ntype="sistema", role="administrador"):
        return Notification(
            title=title,
            message=message,
            notification_type=ntype,
            recipient_role=role,
        )

    @staticmethod
    def demo_admin():
        admin = User(
            first_name="Admin",
            last_name="Sistema",
            address="Comunidad",
            dpi="1234567890101",
            role="administrador",
        )
        admin.set_password("Admin123*")
        return admin

    @staticmethod
    def demo_cistern():
        return Cistern(
            name="Cisterna principal",
            capacity_liters=20000,
            current_liters=12000,
            min_threshold=4000,
            max_threshold=19000,
        )

