import pytest
import os
from datetime import datetime, date
from app import create_app
from app.extensions import db
from app.models import (
    User, House, Resident, Cistern, WaterReading, 
    MonthlyConsumption, Payment, DistributionPlan, 
    MaintenanceOrder, MaintenanceIntervention, Notification
)


@pytest.fixture
def app():
    """Create and configure a test app."""
    import os
    os.environ['TESTING'] = 'true'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's CLI."""
    return app.test_cli_runner()


@pytest.fixture
def auth_user(app):
    """Create an authenticated admin user."""
    with app.app_context():
        user = User(
            first_name="Admin",
            last_name="Test",
            address="Test Address",
            dpi="1111111111111",
            role="administrador"
        )
        user.set_password("Test123*")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    with app.app_context():
        return User.query.get(user_id)


@pytest.fixture
def auth_token(client, auth_user):
    """Get an auth token for the test user."""
    response = client.post('/api/auth/login', json={
        'dpi': '1111111111111',
        'password': 'Test123*'
    })
    return response.get_json()['token']


@pytest.fixture
def auth_headers(auth_token):
    """Get auth headers with token."""
    return {'Authorization': f'Bearer {auth_token}'}


@pytest.fixture
def empleado_user(app):
    """Create an empleado user."""
    with app.app_context():
        user = User(
            first_name="Empleado",
            last_name="Test",
            address="Test Address",
            dpi="2222222222222",
            role="empleado"
        )
        user.set_password("Test123*")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    with app.app_context():
        return User.query.get(user_id)


@pytest.fixture
def soporte_user(app):
    """Create a soporte user."""
    with app.app_context():
        user = User(
            first_name="Soporte",
            last_name="Test",
            address="Test Address",
            dpi="3333333333333",
            role="soporte"
        )
        user.set_password("Test123*")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    with app.app_context():
        return User.query.get(user_id)


@pytest.fixture
def cistern(app):
    """Create a test cistern."""
    with app.app_context():
        cistern = Cistern(
            name="Cisterna Test",
            capacity_liters=20000,
            current_liters=12000,
            min_threshold=4000,
            max_threshold=19000
        )
        db.session.add(cistern)
        db.session.commit()
        cistern_id = cistern.id
    
    with app.app_context():
        return Cistern.query.get(cistern_id)


@pytest.fixture
def house(app):
    """Create a test house."""
    with app.app_context():
        house = House(
            house_number="A-01",
            owner_name="María López",
            address="Sector 1",
            status="activa"
        )
        db.session.add(house)
        db.session.commit()
        house_id = house.id
    
    with app.app_context():
        return House.query.get(house_id)


@pytest.fixture
def houses(app):
    """Create multiple test houses."""
    with app.app_context():
        houses = [
            House(house_number="A-01", owner_name="María López", address="Sector 1", status="activa"),
            House(house_number="A-02", owner_name="Juan Pérez", address="Sector 1", status="activa"),
            House(house_number="A-03", owner_name="Carlos García", address="Sector 2", status="inactiva"),
        ]
        db.session.add_all(houses)
        db.session.commit()
        house_ids = [h.id for h in houses]
    
    with app.app_context():
        return House.query.filter(House.id.in_(house_ids)).all()


@pytest.fixture
def resident(app):
    """Create a test resident."""
    with app.app_context():
        house = House(
            house_number="A-01",
            owner_name="María López",
            address="Sector 1",
            status="activa"
        )
        db.session.add(house)
        db.session.flush()
        
        resident = Resident(
            house_id=house.id,
            first_name="María",
            last_name="López",
            identification="1001",
            is_minor=False
        )
        db.session.add(resident)
        db.session.commit()
        resident_id = resident.id
    
    with app.app_context():
        return Resident.query.get(resident_id)


@pytest.fixture
def water_reading(app):
    """Create a test water reading."""
    with app.app_context():
        cistern = Cistern(
            name="Cisterna Test",
            capacity_liters=20000,
            current_liters=12000,
            min_threshold=4000,
            max_threshold=19000
        )
        db.session.add(cistern)
        db.session.flush()
        
        reading = WaterReading(
            cistern_id=cistern.id,
            liters=12000,
            source="sensor",
            observation="Test reading"
        )
        db.session.add(reading)
        db.session.commit()
        reading_id = reading.id
    
    with app.app_context():
        return WaterReading.query.get(reading_id)


@pytest.fixture
def monthly_consumption(app):
    """Create a test monthly consumption."""
    with app.app_context():
        house = House(
            house_number="A-01",
            owner_name="María López",
            address="Sector 1",
            status="activa"
        )
        db.session.add(house)
        db.session.flush()
        
        consumption = MonthlyConsumption(
            house_id=house.id,
            period="2026-04",
            liters=850,
            observation="Normal",
            is_anomalous=False
        )
        db.session.add(consumption)
        db.session.commit()
        consumption_id = consumption.id
    
    with app.app_context():
        return MonthlyConsumption.query.get(consumption_id)


@pytest.fixture
def payment(app):
    """Create a test payment."""
    with app.app_context():
        house = House(
            house_number="A-01",
            owner_name="María López",
            address="Sector 1",
            status="activa"
        )
        db.session.add(house)
        db.session.flush()
        
        payment = Payment(
            house_id=house.id,
            period="2026-04",
            amount=75.00,
            paid=True,
            receipt_number="REC-001"
        )
        db.session.add(payment)
        db.session.commit()
        payment_id = payment.id
    
    with app.app_context():
        return Payment.query.get(payment_id)


@pytest.fixture
def distribution_plan(app):
    """Create a test distribution plan."""
    with app.app_context():
        from datetime import time
        plan = DistributionPlan(
            service_date=date(2026, 5, 20),
            start_time=time(6, 0),
            end_time=time(12, 0),
            notes="Test distribution"
        )
        db.session.add(plan)
        db.session.commit()
        plan_id = plan.id
    
    with app.app_context():
        return DistributionPlan.query.get(plan_id)


@pytest.fixture
def maintenance_order(app):
    """Create a test maintenance order."""
    with app.app_context():
        order = MaintenanceOrder(
            order_date=date.today(),
            maintenance_type="Preventivo",
            description="Test maintenance",
            responsible="Soporte técnico",
            status="pendiente"
        )
        db.session.add(order)
        db.session.commit()
        order_id = order.id
    
    with app.app_context():
        return MaintenanceOrder.query.get(order_id)


@pytest.fixture
def notification(app):
    """Create a test notification."""
    with app.app_context():
        notif = Notification(
            title="Test Notification",
            message="This is a test notification",
            notification_type="sistema",
            recipient_role="administrador"
        )
        db.session.add(notif)
        db.session.commit()
        notif_id = notif.id
    
    with app.app_context():
        return Notification.query.get(notif_id)
