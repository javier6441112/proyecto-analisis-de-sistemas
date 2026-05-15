import os
from flask import Flask, render_template
from dotenv import load_dotenv
from .extensions import db, migrate, cors


def create_app():
    load_dotenv()
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["JWT_SECRET"] = os.getenv("JWT_SECRET", "dev-jwt-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://agua_user:agua_pass@localhost:5432/agua_db",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    from .routes.auth import auth_bp
    from .routes.api import api_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.cli.command("init-db")
    def init_db_command():
        from .models import User, House, Cistern, WaterReading, Resident, MonthlyConsumption, Payment, MaintenanceOrder, Notification
        db.create_all()
        if not User.query.filter_by(dpi="1234567890101").first():
            admin = User(first_name="Admin", last_name="Sistema", address="Comunidad", dpi="1234567890101", role="administrador")
            admin.set_password("Admin123*")
            db.session.add(admin)
        if not Cistern.query.first():
            cistern = Cistern(name="Cisterna principal", capacity_liters=20000, current_liters=12000, min_threshold=4000, max_threshold=19000)
            db.session.add(cistern)
            db.session.flush()
            db.session.add(WaterReading(cistern_id=cistern.id, liters=12000, source="inicial", observation="Carga inicial"))
        if not House.query.first():
            h1 = House(house_number="A-01", owner_name="María López", address="Sector 1", status="activa")
            h2 = House(house_number="A-02", owner_name="Juan Pérez", address="Sector 1", status="activa")
            db.session.add_all([h1, h2])
            db.session.flush()
            db.session.add_all([
                Resident(house_id=h1.id, first_name="María", last_name="López", identification="1001", is_minor=False),
                Resident(house_id=h1.id, first_name="Ana", last_name="López", identification=None, is_minor=True),
                MonthlyConsumption(house_id=h1.id, period="2026-04", liters=850, observation="Normal"),
                MonthlyConsumption(house_id=h2.id, period="2026-04", liters=1800, observation="Alto", is_anomalous=True),
                Payment(house_id=h1.id, period="2026-04", amount=75, paid=True, receipt_number="REC-001"),
                Payment(house_id=h2.id, period="2026-03", amount=75, paid=True, receipt_number="REC-002"),
            ])
        if not MaintenanceOrder.query.first():
            db.session.add(MaintenanceOrder(maintenance_type="Preventivo", description="Revisión de tuberías principales", responsible="Soporte técnico", status="pendiente"))
        if not Notification.query.first():
            db.session.add(Notification(title="Bienvenido", message="Sistema inicializado correctamente", notification_type="sistema", recipient_role="administrador"))
        db.session.commit()
        print("Base de datos inicializada con datos de prueba.")

    return app
