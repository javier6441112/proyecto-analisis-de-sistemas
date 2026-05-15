from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class User(TimestampMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(180), nullable=False)
    dpi = db.Column(db.String(20), unique=True, nullable=False, index=True)
    role = db.Column(db.String(30), nullable=False, default="empleado")
    password_hash = db.Column(db.String(255), nullable=False)
    failed_attempts = db.Column(db.Integer, default=0, nullable=False)
    is_blocked = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "address": self.address,
            "dpi": self.dpi,
            "role": self.role,
            "isBlocked": self.is_blocked,
        }

class House(TimestampMixin, db.Model):
    __tablename__ = "houses"
    id = db.Column(db.Integer, primary_key=True)
    house_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    owner_name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(180), nullable=False)
    status = db.Column(db.String(30), default="activa", nullable=False)
    residents = db.relationship("Resident", backref="house", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "houseNumber": self.house_number,
            "ownerName": self.owner_name,
            "address": self.address,
            "status": self.status,
            "residentsCount": len(self.residents),
        }

class Resident(TimestampMixin, db.Model):
    __tablename__ = "residents"
    id = db.Column(db.Integer, primary_key=True)
    house_id = db.Column(db.Integer, db.ForeignKey("houses.id"), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    identification = db.Column(db.String(30), nullable=True)
    is_minor = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "houseId": self.house_id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "identification": self.identification,
            "isMinor": self.is_minor,
        }

class Cistern(TimestampMixin, db.Model):
    __tablename__ = "cisterns"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, default="Cisterna comunitaria")
    capacity_liters = db.Column(db.Float, nullable=False)
    current_liters = db.Column(db.Float, nullable=False)
    min_threshold = db.Column(db.Float, nullable=False, default=1000)
    max_threshold = db.Column(db.Float, nullable=True)

    def to_dict(self):
        percentage = 0 if self.capacity_liters == 0 else round((self.current_liters / self.capacity_liters) * 100, 2)
        return {
            "id": self.id,
            "name": self.name,
            "capacityLiters": self.capacity_liters,
            "currentLiters": self.current_liters,
            "minThreshold": self.min_threshold,
            "maxThreshold": self.max_threshold,
            "percentage": percentage,
        }

class WaterReading(TimestampMixin, db.Model):
    __tablename__ = "water_readings"
    id = db.Column(db.Integer, primary_key=True)
    cistern_id = db.Column(db.Integer, db.ForeignKey("cisterns.id"), nullable=False)
    liters = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(30), nullable=False, default="manual")
    observation = db.Column(db.String(255), nullable=True)
    cistern = db.relationship("Cistern", backref="readings")

    def to_dict(self):
        return {
            "id": self.id,
            "cisternId": self.cistern_id,
            "liters": self.liters,
            "source": self.source,
            "observation": self.observation,
            "createdAt": self.created_at.isoformat(),
        }

class MonthlyConsumption(TimestampMixin, db.Model):
    __tablename__ = "monthly_consumptions"
    id = db.Column(db.Integer, primary_key=True)
    house_id = db.Column(db.Integer, db.ForeignKey("houses.id"), nullable=False)
    period = db.Column(db.String(7), nullable=False)  # YYYY-MM
    liters = db.Column(db.Float, nullable=False)
    observation = db.Column(db.String(255), nullable=True)
    is_anomalous = db.Column(db.Boolean, default=False, nullable=False)
    house = db.relationship("House", backref="consumptions")
    __table_args__ = (db.UniqueConstraint("house_id", "period", name="uq_consumption_house_period"),)

    def to_dict(self):
        return {
            "id": self.id,
            "houseId": self.house_id,
            "houseNumber": self.house.house_number if self.house else None,
            "period": self.period,
            "liters": self.liters,
            "observation": self.observation,
            "isAnomalous": self.is_anomalous,
        }

class Payment(TimestampMixin, db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    house_id = db.Column(db.Integer, db.ForeignKey("houses.id"), nullable=False)
    period = db.Column(db.String(7), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    paid = db.Column(db.Boolean, default=True, nullable=False)
    receipt_number = db.Column(db.String(50), nullable=True)
    house = db.relationship("House", backref="payments")
    __table_args__ = (db.UniqueConstraint("house_id", "period", name="uq_payment_house_period"),)

    def to_dict(self):
        return {
            "id": self.id,
            "houseId": self.house_id,
            "houseNumber": self.house.house_number if self.house else None,
            "period": self.period,
            "amount": float(self.amount),
            "paid": self.paid,
            "receiptNumber": self.receipt_number,
        }

class DistributionPlan(TimestampMixin, db.Model):
    __tablename__ = "distribution_plans"
    id = db.Column(db.Integer, primary_key=True)
    service_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    notes = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "serviceDate": self.service_date.isoformat(),
            "startTime": self.start_time.strftime("%H:%M"),
            "endTime": self.end_time.strftime("%H:%M"),
            "notes": self.notes,
        }

class MaintenanceOrder(TimestampMixin, db.Model):
    __tablename__ = "maintenance_orders"
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.Date, nullable=False, default=date.today)
    maintenance_type = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    responsible = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pendiente")
    observations = db.Column(db.Text, nullable=True)
    interventions = db.relationship("MaintenanceIntervention", backref="order", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "orderDate": self.order_date.isoformat(),
            "maintenanceType": self.maintenance_type,
            "description": self.description,
            "responsible": self.responsible,
            "status": self.status,
            "observations": self.observations,
        }

class MaintenanceIntervention(TimestampMixin, db.Model):
    __tablename__ = "maintenance_interventions"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("maintenance_orders.id"), nullable=False)
    intervention_date = db.Column(db.Date, nullable=False, default=date.today)
    intervention_type = db.Column(db.String(80), nullable=False)
    observations = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="finalizada")

    def to_dict(self):
        return {
            "id": self.id,
            "orderId": self.order_id,
            "interventionDate": self.intervention_date.isoformat(),
            "interventionType": self.intervention_type,
            "observations": self.observations,
            "status": self.status,
        }

class Notification(TimestampMixin, db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    notification_type = db.Column(db.String(40), nullable=False)
    recipient_role = db.Column(db.String(30), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "notificationType": self.notification_type,
            "recipientRole": self.recipient_role,
            "isRead": self.is_read,
            "createdAt": self.created_at.isoformat(),
        }
