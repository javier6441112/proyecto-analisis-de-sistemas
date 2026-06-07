from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..factories import ModelFactory
from ..models import Cistern
from ..repositories import (
    CisternRepository, ConsumptionRepository, DistributionPlanRepository,
    HouseRepository, MaintenanceRepository, NotificationRepository,
    PaymentRepository, ResidentRepository, UserRepository, WaterReadingRepository
)
from .auth import VALID_ROLES, login_required, roles_required

api_bp = Blueprint("api", __name__)


def body():
    return request.get_json() or {}


def create_notification(title, message, ntype="sistema", role="administrador"):
    notification = ModelFactory.notification(title, message, ntype, role)
    db.session.add(notification)
    return notification


def evaluate_water_threshold(cistern):
    if cistern.current_liters <= cistern.min_threshold:
        create_notification("Nivel bajo de agua", f"La cisterna tiene {cistern.current_liters:.0f} litros disponibles.", "agua")
    if cistern.max_threshold and cistern.current_liters >= cistern.max_threshold:
        create_notification("Nivel alto de agua", f"La cisterna alcanzó {cistern.current_liters:.0f} litros.", "agua")


def detect_anomaly(house_id, liters):
    avg = ConsumptionRepository().average_liters_for_house(house_id)
    if avg is None:
        return False
    return liters > float(avg) * 1.5


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@api_bp.get("/users")
@roles_required("administrador")
def list_users():
    users = UserRepository().list_recent()
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

    user = ModelFactory.user(data, role=role)
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
    cistern_repo = CisternRepository()
    consumption_repo = ConsumptionRepository()
    notification_repo = NotificationRepository()
    cistern = cistern_repo.latest()
    readings = WaterReadingRepository().list_recent(2)
    daily_consumption = 0
    days_remaining = None
    if len(readings) >= 2:
        daily_consumption = max(0, readings[1].liters - readings[0].liters)
    avg_consumption = consumption_repo.average_liters()
    if cistern and avg_consumption and avg_consumption > 0:
        days_remaining = round(cistern.current_liters / (float(avg_consumption) / 30), 1)
    return jsonify({
        "cistern": cistern.to_dict() if cistern else None,
        "houses": HouseRepository().count(),
        "residents": ResidentRepository().count(),
        "monthlyConsumptionLiters": float(consumption_repo.total_liters()),
        "paymentsTotal": float(PaymentRepository().total_amount()),
        "pendingMaintenance": MaintenanceRepository().pending_count(),
        "unreadNotifications": notification_repo.unread_count_for_role(request.current_user.role),
        "dailyConsumptionLiters": daily_consumption,
        "estimatedDaysRemaining": days_remaining,
        "notifications": [n.to_dict() for n in notification_repo.list_for_role(request.current_user.role, limit=5)],
        "distributionPlans": [p.to_dict() for p in DistributionPlanRepository().list_recent(limit=5)],
    })


@api_bp.get("/cistern")
@roles_required("administrador", "empleado")
def get_cistern():
    cistern = CisternRepository().latest()
    return jsonify(cistern.to_dict() if cistern else {})


@api_bp.post("/cistern")
@roles_required("administrador")
def create_or_update_cistern():
    data = body()
    capacity = float(data.get("capacityLiters", 0))
    current = float(data.get("currentLiters", 0))
    if capacity <= 0 or current < 0 or current > capacity:
        return jsonify({"error": "La capacidad y el nivel deben ser válidos"}), 400
    cistern = CisternRepository().latest() or Cistern(name="Cisterna principal", capacity_liters=capacity, current_liters=current)
    cistern.name = data.get("name", cistern.name)
    cistern.capacity_liters = capacity
    cistern.current_liters = current
    cistern.min_threshold = float(data.get("minThreshold", cistern.min_threshold or 0))
    cistern.max_threshold = float(data["maxThreshold"]) if data.get("maxThreshold") else None
    db.session.add(cistern)
    db.session.flush()
    db.session.add(ModelFactory.water_reading(cistern.id, current, "manual", data.get("observation")))
    evaluate_water_threshold(cistern)
    db.session.commit()
    return jsonify(cistern.to_dict())


@api_bp.post("/sensor")
def sensor_reading():
    data = body()
    cistern = CisternRepository().latest()
    if not cistern:
        return jsonify({"error": "No existe cisterna configurada"}), 400
    liters = float(data.get("liters", -1))
    if liters < 0 or liters > cistern.capacity_liters:
        return jsonify({"error": "Lectura inválida"}), 400
    cistern.current_liters = liters
    reading = ModelFactory.water_reading(cistern.id, liters, "sensor", data.get("observation"))
    db.session.add(reading)
    evaluate_water_threshold(cistern)
    db.session.commit()
    return jsonify({"message": "Lectura recibida", "reading": reading.to_dict()})


@api_bp.get("/water-readings")
@roles_required("administrador", "empleado")
def water_readings():
    return jsonify([r.to_dict() for r in WaterReadingRepository().list_recent(50)])


@api_bp.get("/houses")
@roles_required("administrador", "empleado")
def list_houses():
    return jsonify([h.to_dict() for h in HouseRepository().list_ordered()])


@api_bp.post("/houses")
@roles_required("administrador", "empleado")
def create_house():
    data = body()
    if not data.get("houseNumber") or not data.get("ownerName"):
        return jsonify({"error": "Número de vivienda y propietario son obligatorios"}), 400
    house = ModelFactory.house(data)
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
    if not data.get("houseId") or not data.get("firstName") or not data.get("lastName"):
        return jsonify({"error": "Vivienda, nombre y apellido son obligatorios"}), 400
    resident = ModelFactory.resident(data)
    db.session.add(resident)
    db.session.commit()
    return jsonify(resident.to_dict()), 201


@api_bp.get("/residents")
@roles_required("administrador", "empleado")
def residents():
    house_id = request.args.get("houseId")
    return jsonify([r.to_dict() for r in ResidentRepository().list(house_id)])


@api_bp.get("/consumptions")
@roles_required("administrador", "empleado")
def list_consumptions():
    house_id = request.args.get("houseId")
    return jsonify([c.to_dict() for c in ConsumptionRepository().list(house_id)])


@api_bp.post("/consumptions")
@roles_required("administrador", "empleado")
def create_consumption():
    data = body()
    liters = float(data.get("liters", 0))
    if not data.get("houseId") or not data.get("period") or liters < 0:
        return jsonify({"error": "Vivienda, período y litros válidos son obligatorios"}), 400
    anomalous = detect_anomaly(int(data["houseId"]), liters)
    consumption = ModelFactory.monthly_consumption(data, is_anomalous=anomalous)
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
    return jsonify([p.to_dict() for p in PaymentRepository().list_ordered()])


@api_bp.post("/payments")
@roles_required("administrador", "empleado")
def create_payment():
    data = body()
    if not data.get("houseId") or not data.get("period") or not data.get("amount"):
        return jsonify({"error": "Vivienda, período y monto son obligatorios"}), 400
    payment = ModelFactory.payment(data)
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
    payment_repo = PaymentRepository()
    for house in HouseRepository().list_all():
        paid_count = payment_repo.paid_count_for_periods(house.id, periods)
        if len(periods) - paid_count >= 2:
            result.append(house.to_dict())
    return jsonify(result)


@api_bp.get("/distribution-plans")
@login_required
def list_distribution():
    return jsonify([p.to_dict() for p in DistributionPlanRepository().list_recent()])


@api_bp.post("/distribution-plans")
@roles_required("administrador")
def create_distribution():
    data = body()
    plan = ModelFactory.distribution_plan(data)
    if plan.start_time >= plan.end_time:
        return jsonify({"error": "La hora de inicio debe ser menor a la hora final"}), 400
    overlap = DistributionPlanRepository().find_overlap(plan.service_date, plan.start_time, plan.end_time)
    if overlap:
        return jsonify({"error": "El horario se traslapa con otra planificación"}), 409
    db.session.add(plan)
    db.session.commit()
    return jsonify(plan.to_dict()), 201


@api_bp.get("/maintenance-orders")
@login_required
def maintenance_orders():
    return jsonify([o.to_dict() for o in MaintenanceRepository().list_orders()])


@api_bp.post("/maintenance-orders")
@roles_required("administrador", "soporte")
def create_maintenance_order():
    data = body()
    order = ModelFactory.maintenance_order(data)
    db.session.add(order)
    create_notification("Orden de mantenimiento", f"Nueva orden creada para {order.responsible}", "mantenimiento", "soporte")
    db.session.commit()
    return jsonify(order.to_dict()), 201


@api_bp.post("/maintenance-interventions")
@roles_required("administrador", "soporte")
def create_intervention():
    data = body()
    intervention = ModelFactory.maintenance_intervention(data)
    order = MaintenanceRepository().get_order_or_404(intervention.order_id)
    order.status = intervention.status
    db.session.add(intervention)
    db.session.commit()
    return jsonify(intervention.to_dict()), 201


@api_bp.get("/notifications")
@login_required
def notifications():
    current_role = request.current_user.role
    notifications = NotificationRepository().list_for_role(current_role)
    return jsonify([n.to_dict() for n in notifications])


@api_bp.post("/notifications/<int:notification_id>/read")
@login_required
def mark_notification_read(notification_id):
    notification = NotificationRepository().get_or_404(notification_id)
    notification.is_read = True
    db.session.commit()
    return jsonify(notification.to_dict())
