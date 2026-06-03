from datetime import datetime, date
from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import (
    Cistern, DistributionPlan, House, MaintenanceIntervention, MaintenanceOrder,
    MonthlyConsumption, Notification, Payment, Resident, User, WaterReading
)
from .auth import VALID_ROLES, login_required, roles_required

api_bp = Blueprint("api", __name__)


def body():
    return request.get_json() or {}


def create_notification(title, message, ntype="sistema", role="administrador"):
    notification = Notification(title=title, message=message, notification_type=ntype, recipient_role=role)
    db.session.add(notification)
    return notification


def evaluate_water_threshold(cistern):
    if cistern.current_liters <= cistern.min_threshold:
        create_notification("Nivel bajo de agua", f"La cisterna tiene {cistern.current_liters:.0f} litros disponibles.", "agua")
    if cistern.max_threshold and cistern.current_liters >= cistern.max_threshold:
        create_notification("Nivel alto de agua", f"La cisterna alcanzó {cistern.current_liters:.0f} litros.", "agua")


def detect_anomaly(house_id, liters):
    avg = db.session.query(func.avg(MonthlyConsumption.liters)).filter(MonthlyConsumption.house_id == house_id).scalar()
    if avg is None:
        return False
    return liters > float(avg) * 1.5


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@api_bp.get("/users")
@roles_required("administrador")
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([user.to_dict() for user in users])


@api_bp.post("/users")
@roles_required("administrador")
def create_user():
    data = body()
    required = ["firstName", "lastName", "address", "dpi", "role", "password", "confirmPassword"]
    if any(not str(data.get(field, "")).strip() for field in required):
        return jsonify({"error": "Todos los campos obligatorios deben completarse"}), 400
    if data["password"] != data["confirmPassword"]:
        return jsonify({"error": "Las contraseñas no coinciden"}), 400
    if len(data["password"]) < 8:
        return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400

    role = data["role"].strip()
    if role not in VALID_ROLES:
        return jsonify({"error": "Rol inválido"}), 400

    user = User(
        first_name=data["firstName"].strip(),
        last_name=data["lastName"].strip(),
        address=data["address"].strip(),
        dpi=data["dpi"].strip(),
        role=role,
    )
    user.set_password(data["password"])
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "El DPI ya está registrado"}), 409
    return jsonify({"message": "Usuario creado correctamente", "user": user.to_dict()}), 201


@api_bp.get("/dashboard")
@roles_required("administrador", "empleado", "soporte")
def dashboard():
    cistern = Cistern.query.order_by(Cistern.id.desc()).first()
    readings = WaterReading.query.order_by(WaterReading.created_at.desc()).limit(2).all()
    daily_consumption = 0
    days_remaining = None
    if len(readings) >= 2:
        daily_consumption = max(0, readings[1].liters - readings[0].liters)
    avg_consumption = db.session.query(func.avg(MonthlyConsumption.liters)).scalar()
    if cistern and avg_consumption and avg_consumption > 0:
        days_remaining = round(cistern.current_liters / (float(avg_consumption) / 30), 1)
    notifications_query = Notification.query.order_by(Notification.created_at.desc()).filter(
        or_(Notification.recipient_role.is_(None), Notification.recipient_role == request.current_user.role)
    )
    return jsonify({
        "cistern": cistern.to_dict() if cistern else None,
        "houses": House.query.count(),
        "residents": Resident.query.count(),
        "monthlyConsumptionLiters": float(db.session.query(func.coalesce(func.sum(MonthlyConsumption.liters), 0)).scalar()),
        "paymentsTotal": float(db.session.query(func.coalesce(func.sum(Payment.amount), 0)).scalar()),
        "pendingMaintenance": MaintenanceOrder.query.filter(MaintenanceOrder.status != "finalizada").count(),
        "unreadNotifications": notifications_query.filter_by(is_read=False).count(),
        "dailyConsumptionLiters": daily_consumption,
        "estimatedDaysRemaining": days_remaining,
        "notifications": [n.to_dict() for n in notifications_query.limit(5).all()],
        "distributionPlans": [p.to_dict() for p in DistributionPlan.query.order_by(DistributionPlan.service_date.desc()).limit(5).all()],
    })


@api_bp.get("/cistern")
@roles_required("administrador", "empleado")
def get_cistern():
    cistern = Cistern.query.order_by(Cistern.id.desc()).first()
    return jsonify(cistern.to_dict() if cistern else {})


@api_bp.post("/cistern")
@roles_required("administrador")
def create_or_update_cistern():
    data = body()
    capacity = float(data.get("capacityLiters", 0))
    current = float(data.get("currentLiters", 0))
    if capacity <= 0 or current < 0 or current > capacity:
        return jsonify({"error": "La capacidad y el nivel deben ser válidos"}), 400
    cistern = Cistern.query.order_by(Cistern.id.desc()).first() or Cistern(name="Cisterna principal", capacity_liters=capacity, current_liters=current)
    cistern.name = data.get("name", cistern.name)
    cistern.capacity_liters = capacity
    cistern.current_liters = current
    cistern.min_threshold = float(data.get("minThreshold", cistern.min_threshold or 0))
    cistern.max_threshold = float(data["maxThreshold"]) if data.get("maxThreshold") else None
    db.session.add(cistern)
    db.session.flush()
    db.session.add(WaterReading(cistern_id=cistern.id, liters=current, source="manual", observation=data.get("observation")))
    evaluate_water_threshold(cistern)
    db.session.commit()
    return jsonify(cistern.to_dict())


@api_bp.post("/sensor")
def sensor_reading():
    data = body()
    cistern = Cistern.query.order_by(Cistern.id.desc()).first()
    if not cistern:
        return jsonify({"error": "No existe cisterna configurada"}), 400
    liters = float(data.get("liters", -1))
    if liters < 0 or liters > cistern.capacity_liters:
        return jsonify({"error": "Lectura inválida"}), 400
    cistern.current_liters = liters
    reading = WaterReading(cistern_id=cistern.id, liters=liters, source="sensor", observation=data.get("observation"))
    db.session.add(reading)
    evaluate_water_threshold(cistern)
    db.session.commit()
    return jsonify({"message": "Lectura recibida", "reading": reading.to_dict()})


@api_bp.get("/water-readings")
@roles_required("administrador", "empleado")
def water_readings():
    return jsonify([r.to_dict() for r in WaterReading.query.order_by(WaterReading.created_at.desc()).limit(50).all()])


@api_bp.get("/houses")
@roles_required("administrador", "empleado")
def list_houses():
    return jsonify([h.to_dict() for h in House.query.order_by(House.house_number).all()])


@api_bp.post("/houses")
@roles_required("administrador", "empleado")
def create_house():
    data = body()
    if not data.get("houseNumber") or not data.get("ownerName"):
        return jsonify({"error": "Número de vivienda y propietario son obligatorios"}), 400
    house = House(house_number=data["houseNumber"], owner_name=data["ownerName"], address=data.get("address", "Sin dirección"), status=data.get("status", "activa"))
    db.session.add(house)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe una vivienda con ese número"}), 409
    return jsonify(house.to_dict()), 201


@api_bp.post("/residents")
@roles_required("administrador", "empleado")
def create_resident():
    data = body()
    is_minor = bool(data.get("isMinor", False))
    if not data.get("houseId") or not data.get("firstName") or not data.get("lastName"):
        return jsonify({"error": "Vivienda, nombre y apellido son obligatorios"}), 400
    resident = Resident(house_id=int(data["houseId"]), first_name=data["firstName"], last_name=data["lastName"], is_minor=is_minor, identification=None if is_minor else data.get("identification"))
    db.session.add(resident)
    db.session.commit()
    return jsonify(resident.to_dict()), 201


@api_bp.get("/residents")
@roles_required("administrador", "empleado")
def residents():
    house_id = request.args.get("houseId")
    q = Resident.query
    if house_id:
        q = q.filter_by(house_id=house_id)
    return jsonify([r.to_dict() for r in q.order_by(Resident.last_name).all()])


@api_bp.get("/consumptions")
@roles_required("administrador", "empleado")
def list_consumptions():
    house_id = request.args.get("houseId")
    q = MonthlyConsumption.query
    if house_id:
        q = q.filter_by(house_id=house_id)
    return jsonify([c.to_dict() for c in q.order_by(MonthlyConsumption.period.desc()).all()])


@api_bp.post("/consumptions")
@roles_required("administrador", "empleado")
def create_consumption():
    data = body()
    liters = float(data.get("liters", 0))
    if not data.get("houseId") or not data.get("period") or liters < 0:
        return jsonify({"error": "Vivienda, período y litros válidos son obligatorios"}), 400
    anomalous = detect_anomaly(int(data["houseId"]), liters)
    consumption = MonthlyConsumption(house_id=int(data["houseId"]), period=data["period"], liters=liters, observation=data.get("observation"), is_anomalous=anomalous)
    db.session.add(consumption)
    if anomalous:
        create_notification("Consumo anómalo", f"La vivienda ID {data['houseId']} registró un consumo fuera del patrón esperado.", "consumo")
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe consumo para esa vivienda y período"}), 409
    return jsonify(consumption.to_dict()), 201


@api_bp.get("/payments")
@roles_required("administrador", "empleado")
def list_payments():
    return jsonify([p.to_dict() for p in Payment.query.order_by(Payment.period.desc()).all()])


@api_bp.post("/payments")
@roles_required("administrador", "empleado")
def create_payment():
    data = body()
    if not data.get("houseId") or not data.get("period") or not data.get("amount"):
        return jsonify({"error": "Vivienda, período y monto son obligatorios"}), 400
    payment = Payment(house_id=int(data["houseId"]), period=data["period"], amount=data["amount"], paid=True, receipt_number=data.get("receiptNumber"))
    db.session.add(payment)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Esta vivienda ya pagó ese período"}), 409
    return jsonify(payment.to_dict()), 201


@api_bp.get("/delinquency")
@roles_required("administrador", "empleado")
def delinquency():
    periods = request.args.getlist("period")
    if not periods:
        periods = ["2026-03", "2026-04"]
    result = []
    for house in House.query.all():
        paid_count = Payment.query.filter(Payment.house_id == house.id, Payment.period.in_(periods), Payment.paid.is_(True)).count()
        if len(periods) - paid_count >= 2:
            result.append(house.to_dict())
    return jsonify(result)


@api_bp.get("/distribution-plans")
@login_required
def list_distribution():
    return jsonify([p.to_dict() for p in DistributionPlan.query.order_by(DistributionPlan.service_date.desc()).all()])


@api_bp.post("/distribution-plans")
@roles_required("administrador")
def create_distribution():
    data = body()
    service_date = datetime.strptime(data["serviceDate"], "%Y-%m-%d").date()
    start_time = datetime.strptime(data["startTime"], "%H:%M").time()
    end_time = datetime.strptime(data["endTime"], "%H:%M").time()
    if start_time >= end_time:
        return jsonify({"error": "La hora de inicio debe ser menor a la hora final"}), 400
    overlap = DistributionPlan.query.filter(
        DistributionPlan.service_date == service_date,
        DistributionPlan.start_time < end_time,
        DistributionPlan.end_time > start_time,
    ).first()
    if overlap:
        return jsonify({"error": "El horario se traslapa con otra planificación"}), 409
    plan = DistributionPlan(service_date=service_date, start_time=start_time, end_time=end_time, notes=data.get("notes"))
    db.session.add(plan)
    db.session.commit()
    return jsonify(plan.to_dict()), 201


@api_bp.get("/maintenance-orders")
@login_required
def maintenance_orders():
    return jsonify([o.to_dict() for o in MaintenanceOrder.query.order_by(MaintenanceOrder.order_date.desc()).all()])


@api_bp.post("/maintenance-orders")
@roles_required("administrador", "soporte")
def create_maintenance_order():
    data = body()
    order = MaintenanceOrder(
        order_date=datetime.strptime(data.get("orderDate", date.today().isoformat()), "%Y-%m-%d").date(),
        maintenance_type=data.get("maintenanceType", "Correctivo"),
        description=data.get("description", "Sin descripción"),
        responsible=data.get("responsible", "Soporte técnico"),
        observations=data.get("observations"),
    )
    db.session.add(order)
    create_notification("Orden de mantenimiento", f"Nueva orden creada para {order.responsible}", "mantenimiento", "soporte")
    db.session.commit()
    return jsonify(order.to_dict()), 201


@api_bp.post("/maintenance-interventions")
@roles_required("administrador", "soporte")
def create_intervention():
    data = body()
    intervention = MaintenanceIntervention(order_id=int(data["orderId"]), intervention_type=data.get("interventionType", "Revisión"), observations=data.get("observations"), status=data.get("status", "finalizada"))
    order = MaintenanceOrder.query.get_or_404(intervention.order_id)
    order.status = intervention.status
    db.session.add(intervention)
    db.session.commit()
    return jsonify(intervention.to_dict()), 201


@api_bp.get("/notifications")
@login_required
def notifications():
    current_role = request.current_user.role
    notifications = Notification.query.order_by(Notification.created_at.desc()).filter(
        or_(Notification.recipient_role.is_(None), Notification.recipient_role == current_role)
    ).all()
    return jsonify([n.to_dict() for n in notifications])


@api_bp.post("/notifications/<int:notification_id>/read")
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    notification.is_read = True
    db.session.commit()
    return jsonify(notification.to_dict())
