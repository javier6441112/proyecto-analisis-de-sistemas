import pytest
from datetime import date, time, timedelta
from app.extensions import db
from app.models import (
    User, House, Resident, Cistern, WaterReading,
    MonthlyConsumption, Payment, DistributionPlan,
    MaintenanceOrder, MaintenanceIntervention, Notification
)


class TestUserModel:
    """Test User model."""
    
    def test_user_creation(self, app):
        """Test creating a user."""
        with app.app_context():
            user = User(
                first_name="John",
                last_name="Doe",
                address="123 Main St",
                dpi="1234567890123",
                role="empleado"
            )
            user.set_password("SecurePass123*")
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.first_name == "John"
            assert user.role == "empleado"
    
    def test_user_password_hashing(self, app):
        """Test password hashing and verification."""
        with app.app_context():
            user = User(
                first_name="Jane",
                last_name="Doe",
                address="123 Main St",
                dpi="9876543210123",
                role="administrador"
            )
            user.set_password("MyPassword123!")
            db.session.add(user)
            db.session.commit()
            
            assert user.check_password("MyPassword123!")
            assert not user.check_password("WrongPassword")
    
    def test_user_to_dict(self, auth_user):
        """Test user to_dict conversion."""
        user_dict = auth_user.to_dict()
        assert "id" in user_dict
        assert user_dict["firstName"] == "Admin"
        assert user_dict["role"] == "administrador"
        assert "password_hash" not in user_dict
    
    def test_user_failed_attempts(self, app):
        """Test user failed login attempts."""
        with app.app_context():
            user = User(
                first_name="Test",
                last_name="User",
                address="Test",
                dpi="5555555555555",
                role="empleado"
            )
            user.set_password("Test123*")
            db.session.add(user)
            db.session.commit()
            
            assert user.failed_attempts == 0
            
            user.failed_attempts = 5
            user.is_blocked = True
            db.session.commit()
            
            user_retrieved = User.query.filter_by(dpi="5555555555555").first()
            assert user_retrieved.is_blocked == True


class TestHouseModel:
    """Test House model."""
    
    def test_house_creation(self, house):
        """Test creating a house."""
        assert house.id is not None
        assert house.house_number == "A-01"
        assert house.status == "activa"
    
    def test_house_to_dict(self, app):
        """Test house to_dict conversion."""
        with app.app_context():
            house = House(
                house_number="A-01",
                owner_name="María López",
                address="Sector 1",
                status="activa"
            )
            db.session.add(house)
            db.session.commit()
            
            house_dict = house.to_dict()
            assert house_dict["houseNumber"] == "A-01"
            assert house_dict["ownerName"] == "María López"
    
    def test_house_with_residents(self, app, house):
        """Test house with residents relationship."""
        with app.app_context():
            resident = Resident(
                house_id=house.id,
                first_name="Carlos",
                last_name="López",
                identification="1002",
                is_minor=False
            )
            db.session.add(resident)
            db.session.commit()
            
            house_updated = House.query.get(house.id)
            assert len(house_updated.residents) == 1


class TestResidentModel:
    """Test Resident model."""
    
    def test_resident_creation(self, resident):
        """Test creating a resident."""
        assert resident.id is not None
        assert resident.first_name == "María"
        assert resident.is_minor == False
    
    def test_resident_minor(self, app, house):
        """Test creating a minor resident."""
        with app.app_context():
            minor = Resident(
                house_id=house.id,
                first_name="Ana",
                last_name="López",
                identification=None,
                is_minor=True
            )
            db.session.add(minor)
            db.session.commit()
            
            assert minor.is_minor == True
            assert minor.identification is None
    
    def test_resident_to_dict(self, resident):
        """Test resident to_dict conversion."""
        resident_dict = resident.to_dict()
        assert resident_dict["firstName"] == "María"
        assert resident_dict["isMinor"] == False


class TestCisternModel:
    """Test Cistern model."""
    
    def test_cistern_creation(self, cistern):
        """Test creating a cistern."""
        assert cistern.id is not None
        assert cistern.capacity_liters == 20000
        assert cistern.current_liters == 12000
    
    def test_cistern_to_dict(self, cistern):
        """Test cistern to_dict conversion."""
        cistern_dict = cistern.to_dict()
        assert cistern_dict["name"] == "Cisterna Test"
        assert cistern_dict["percentage"] == 60.0
    
    def test_cistern_percentage_calculation(self, app):
        """Test cistern percentage calculation."""
        with app.app_context():
            cistern = Cistern(
                name="Test",
                capacity_liters=1000,
                current_liters=500,
                min_threshold=100
            )
            cistern_dict = cistern.to_dict()
            assert cistern_dict["percentage"] == 50.0


class TestWaterReadingModel:
    """Test WaterReading model."""
    
    def test_water_reading_creation(self, water_reading):
        """Test creating a water reading."""
        assert water_reading.id is not None
        assert water_reading.liters == 12000
        assert water_reading.source == "sensor"
    
    def test_water_reading_to_dict(self, water_reading):
        """Test water reading to_dict conversion."""
        reading_dict = water_reading.to_dict()
        assert reading_dict["liters"] == 12000
        assert "createdAt" in reading_dict


class TestMonthlyConsumptionModel:
    """Test MonthlyConsumption model."""
    
    def test_consumption_creation(self, monthly_consumption):
        """Test creating a consumption record."""
        assert monthly_consumption.id is not None
        assert monthly_consumption.period == "2026-04"
        assert monthly_consumption.liters == 850
    
    def test_consumption_anomalous(self, app, house):
        """Test consumption anomalous flag."""
        with app.app_context():
            consumption = MonthlyConsumption(
                house_id=house.id,
                period="2026-05",
                liters=2500,
                is_anomalous=True
            )
            db.session.add(consumption)
            db.session.commit()
            
            assert consumption.is_anomalous == True
    
    def test_consumption_to_dict(self, app):
        """Test consumption to_dict conversion."""
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
            
            consumption_dict = consumption.to_dict()
            assert consumption_dict["period"] == "2026-04"
            assert consumption_dict["isAnomalous"] == False


class TestPaymentModel:
    """Test Payment model."""
    
    def test_payment_creation(self, payment):
        """Test creating a payment."""
        assert payment.id is not None
        assert payment.period == "2026-04"
        assert float(payment.amount) == 75.0
        assert payment.paid == True
    
    def test_payment_to_dict(self, app):
        """Test payment to_dict conversion."""
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
            
            payment_dict = payment.to_dict()
            assert payment_dict["period"] == "2026-04"
            assert payment_dict["amount"] == 75.0


class TestDistributionPlanModel:
    """Test DistributionPlan model."""
    
    def test_distribution_plan_creation(self, distribution_plan):
        """Test creating a distribution plan."""
        assert distribution_plan.id is not None
        assert distribution_plan.service_date == date(2026, 5, 20)
    
    def test_distribution_plan_to_dict(self, distribution_plan):
        """Test distribution plan to_dict conversion."""
        plan_dict = distribution_plan.to_dict()
        assert plan_dict["serviceDate"] == "2026-05-20"
        assert plan_dict["startTime"] == "06:00"


class TestMaintenanceOrderModel:
    """Test MaintenanceOrder model."""
    
    def test_maintenance_order_creation(self, maintenance_order):
        """Test creating a maintenance order."""
        assert maintenance_order.id is not None
        assert maintenance_order.maintenance_type == "Preventivo"
        assert maintenance_order.status == "pendiente"
    
    def test_maintenance_order_to_dict(self, maintenance_order):
        """Test maintenance order to_dict conversion."""
        order_dict = maintenance_order.to_dict()
        assert order_dict["maintenanceType"] == "Preventivo"
        assert order_dict["status"] == "pendiente"


class TestNotificationModel:
    """Test Notification model."""
    
    def test_notification_creation(self, notification):
        """Test creating a notification."""
        assert notification.id is not None
        assert notification.title == "Test Notification"
        assert notification.is_read == False
    
    def test_notification_mark_as_read(self, app):
        """Test marking notification as read."""
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
            
            # Mark as read
            notif.is_read = True
            db.session.commit()
            
            notif_retrieved = Notification.query.get(notif_id)
            assert notif_retrieved.is_read == True
