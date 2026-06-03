from datetime import datetime, timedelta
from functools import wraps
import jwt
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)

VALID_ROLES = {"administrador", "empleado", "soporte", "cliente"}


def create_token(user: User):
    payload = {
        "sub": str(user.id),
        "dpi": user.dpi,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(hours=8),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def current_user_from_request():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.replace("Bearer ", "", 1)
    try:
        payload = jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    return User.query.get(int(payload["sub"]))


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user_from_request()
        if not user:
            return jsonify({"error": "No autenticado o token inválido"}), 401
        request.current_user = user
        return fn(*args, **kwargs)
    return wrapper


def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user_from_request()
            if not user:
                return jsonify({"error": "No autenticado o token inválido"}), 401
            if user.role not in roles:
                return jsonify({"error": "No tienes permisos para realizar esta acción"}), 403
            request.current_user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    required = ["firstName", "lastName", "address", "dpi", "password", "confirmPassword"]
    if any(not str(data.get(field, "")).strip() for field in required):
        return jsonify({"error": "Todos los campos obligatorios deben completarse"}), 400
    if data["password"] != data["confirmPassword"]:
        return jsonify({"error": "Las contraseñas no coinciden"}), 400
    if len(data["password"]) < 8:
        return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400
    user = User(
        first_name=data["firstName"].strip(),
        last_name=data["lastName"].strip(),
        address=data["address"].strip(),
        dpi=data["dpi"].strip(),
        role="cliente",
    )
    user.set_password(data["password"])
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "El DPI ya está registrado"}), 409
    return jsonify({"message": "Usuario registrado correctamente", "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    dpi = str(data.get("dpi", "")).strip()
    password = str(data.get("password", ""))
    if not dpi or not password:
        return jsonify({"error": "DPI y contraseña son obligatorios"}), 400
    user = User.query.filter_by(dpi=dpi).first()
    if not user:
        return jsonify({"error": "Usuario no registrado"}), 404
    if user.is_blocked:
        return jsonify({"error": "Cuenta bloqueada por intentos fallidos"}), 423
    if not user.check_password(password):
        user.failed_attempts += 1
        if user.failed_attempts >= 5:
            user.is_blocked = True
        db.session.commit()
        return jsonify({"error": "Credenciales incorrectas"}), 401
    user.failed_attempts = 0
    db.session.commit()
    return jsonify({"token": create_token(user), "user": user.to_dict()})


@auth_bp.get("/me")
@login_required
def me():
    return jsonify(request.current_user.to_dict())
