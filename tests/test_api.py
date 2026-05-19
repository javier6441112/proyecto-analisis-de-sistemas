import pytest
from datetime import date, time
from app.extensions import db
from app.models import (
    House, Resident, Cistern, WaterReading, MonthlyConsumption,
    Payment, DistributionPlan, MaintenanceOrder, Notification
)


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/api/health')
        assert response.status_code == 200
        assert response.get_json()['status'] == 'ok'


class TestDashboard:
    """Test dashboard endpoint."""
    
    def test_dashboard_admin(self, client, auth_headers, cistern, house):
        """Test dashboard for admin user."""
        response = client.get('/api/dashboard', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'cistern' in data
        assert 'houses' in data
        assert 'residents' in data
    
    def test_dashboard_without_auth(self, client):
        """Test dashboard without authentication."""
        response = client.get('/api/dashboard')
        assert response.status_code == 401
    
    def test_dashboard_with_data(self, app, client, auth_headers, cistern, house):
        """Test dashboard with populated data."""
        with app.app_context():
            reading = WaterReading(cistern_id=cistern.id, liters=12000, source="sensor")
            db.session.add(reading)
            db.session.commit()
        
        response = client.get('/api/dashboard', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['cistern'] is not None
        assert data['houses'] == 1


class TestCisternEndpoints:
    """Test cistern endpoints."""
    
    def test_get_cistern(self, client, auth_headers, cistern):
        """Test getting cistern info."""
        response = client.get('/api/cistern', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['capacityLiters'] == 20000
        assert data['currentLiters'] == 12000
    
    def test_create_cistern_admin(self, client, auth_headers):
        """Test creating/updating cistern as admin."""
        response = client.post('/api/cistern', headers=auth_headers, json={
            'capacityLiters': 25000,
            'currentLiters': 15000,
            'minThreshold': 5000,
            'maxThreshold': 24000,
            'name': 'New Cistern'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['capacityLiters'] == 25000
    
    def test_create_cistern_invalid_capacity(self, client, auth_headers):
        """Test creating cistern with invalid capacity."""
        response = client.post('/api/cistern', headers=auth_headers, json={
            'capacityLiters': 0,
            'currentLiters': 15000
        })
        assert response.status_code == 400
    
    def test_create_cistern_current_exceeds_capacity(self, client, auth_headers):
        """Test creating cistern with current > capacity."""
        response = client.post('/api/cistern', headers=auth_headers, json={
            'capacityLiters': 20000,
            'currentLiters': 25000
        })
        assert response.status_code == 400


class TestSensorReading:
    """Test sensor reading endpoint."""
    
    def test_sensor_reading_success(self, client, app, cistern):
        """Test successful sensor reading."""
        response = client.post('/api/sensor', json={
            'liters': 10000,
            'observation': 'Sensor reading'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Lectura recibida'
    
    def test_sensor_reading_no_cistern(self, client):
        """Test sensor reading with no cistern."""
        response = client.post('/api/sensor', json={
            'liters': 10000
        })
        assert response.status_code == 400
    
    def test_sensor_reading_invalid_liters(self, client, cistern):
        """Test sensor reading with invalid liters."""
        response = client.post('/api/sensor', json={
            'liters': -100
        })
        assert response.status_code == 400
        
        response = client.post('/api/sensor', json={
            'liters': 50000
        })
        assert response.status_code == 400


class TestWaterReadings:
    """Test water readings endpoint."""
    
    def test_water_readings_list(self, client, auth_headers, water_reading):
        """Test listing water readings."""
        response = client.get('/api/water-readings', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
        assert data[0]['liters'] == 12000


class TestHousesEndpoints:
    """Test houses endpoints."""
    
    def test_list_houses(self, client, auth_headers, houses):
        """Test listing houses."""
        response = client.get('/api/houses', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 3
        assert data[0]['houseNumber'] == 'A-01'
    
    def test_create_house(self, client, auth_headers):
        """Test creating a house."""
        response = client.post('/api/houses', headers=auth_headers, json={
            'houseNumber': 'B-01',
            'ownerName': 'Carlos López',
            'address': 'Sector 2',
            'status': 'activa'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['houseNumber'] == 'B-01'
    
    def test_create_house_missing_fields(self, client, auth_headers):
        """Test creating house with missing fields."""
        response = client.post('/api/houses', headers=auth_headers, json={
            'houseNumber': 'B-02'
        })
        assert response.status_code == 400
    
    def test_create_house_duplicate(self, client, auth_headers, house):
        """Test creating duplicate house."""
        response = client.post('/api/houses', headers=auth_headers, json={
            'houseNumber': 'A-01',
            'ownerName': 'Different Owner'
        })
        assert response.status_code == 409


class TestResidentsEndpoints:
    """Test residents endpoints."""
    
    def test_list_residents(self, client, auth_headers, resident):
        """Test listing residents."""
        response = client.get('/api/residents', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
    
    def test_list_residents_by_house(self, client, auth_headers, resident):
        """Test listing residents by house."""
        response = client.get(f'/api/residents?houseId={resident.house_id}', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
        assert data[0]['houseId'] == resident.house_id
    
    def test_create_resident(self, client, auth_headers, house):
        """Test creating a resident."""
        response = client.post('/api/residents', headers=auth_headers, json={
            'houseId': house.id,
            'firstName': 'Pedro',
            'lastName': 'García',
            'identification': '2001',
            'isMinor': False
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['firstName'] == 'Pedro'
    
    def test_create_minor_resident(self, client, auth_headers, house):
        """Test creating a minor resident."""
        response = client.post('/api/residents', headers=auth_headers, json={
            'houseId': house.id,
            'firstName': 'Ana',
            'lastName': 'García',
            'isMinor': True
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['isMinor'] == True
        assert data['identification'] is None


class TestConsumptionEndpoints:
    """Test consumption endpoints."""
    
    def test_list_consumptions(self, client, auth_headers, monthly_consumption):
        """Test listing consumptions."""
        response = client.get('/api/consumptions', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
    
    def test_list_consumptions_by_house(self, client, auth_headers, monthly_consumption):
        """Test listing consumptions by house."""
        response = client.get(f'/api/consumptions?houseId={monthly_consumption.house_id}', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
    
    def test_create_consumption(self, client, auth_headers, house):
        """Test creating a consumption."""
        response = client.post('/api/consumptions', headers=auth_headers, json={
            'houseId': house.id,
            'period': '2026-05',
            'liters': 900,
            'observation': 'Normal'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['period'] == '2026-05'
    
    def test_create_consumption_invalid_data(self, client, auth_headers):
        """Test creating consumption with invalid data."""
        response = client.post('/api/consumptions', headers=auth_headers, json={
            'period': '2026-05',
            'liters': 900
        })
        assert response.status_code == 400


class TestPaymentEndpoints:
    """Test payment endpoints."""
    
    def test_list_payments(self, client, auth_headers, payment):
        """Test listing payments."""
        response = client.get('/api/payments', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
    
    def test_create_payment(self, client, auth_headers, house):
        """Test creating a payment."""
        response = client.post('/api/payments', headers=auth_headers, json={
            'houseId': house.id,
            'period': '2026-05',
            'amount': 75.00,
            'receiptNumber': 'REC-002'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert float(data['amount']) == 75.0
    
    def test_create_payment_missing_fields(self, client, auth_headers):
        """Test creating payment with missing fields."""
        response = client.post('/api/payments', headers=auth_headers, json={
            'houseId': 1,
            'period': '2026-05'
        })
        assert response.status_code == 400


class TestDelinquencyEndpoint:
    """Test delinquency endpoint."""
    
    def test_delinquency_list(self, client, auth_headers, house):
        """Test getting delinquent houses."""
        response = client.get('/api/delinquency', headers=auth_headers)
        assert response.status_code == 200
    
    def test_delinquency_with_periods(self, client, auth_headers, house):
        """Test delinquency with specific periods."""
        response = client.get('/api/delinquency?period=2026-03&period=2026-04', headers=auth_headers)
        assert response.status_code == 200


class TestDistributionPlanEndpoints:
    """Test distribution plan endpoints."""
    
    def test_list_distribution_plans(self, client, auth_headers, distribution_plan):
        """Test listing distribution plans."""
        response = client.get('/api/distribution-plans', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
    
    def test_create_distribution_plan(self, client, auth_headers):
        """Test creating a distribution plan."""
        response = client.post('/api/distribution-plans', headers=auth_headers, json={
            'serviceDate': '2026-05-21',
            'startTime': '08:00',
            'endTime': '14:00',
            'notes': 'New plan'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['serviceDate'] == '2026-05-21'
    
    def test_create_distribution_plan_invalid_times(self, client, auth_headers):
        """Test creating distribution plan with invalid times."""
        response = client.post('/api/distribution-plans', headers=auth_headers, json={
            'serviceDate': '2026-05-21',
            'startTime': '14:00',
            'endTime': '08:00'
        })
        assert response.status_code == 400


class TestMaintenanceOrderEndpoints:
    """Test maintenance order endpoints."""
    
    def test_list_maintenance_orders(self, client, auth_headers, maintenance_order):
        """Test listing maintenance orders."""
        response = client.get('/api/maintenance-orders', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
    
    def test_create_maintenance_order(self, client, auth_headers, soporte_user):
        """Test creating maintenance order."""
        from app.routes.auth import create_token
        token = create_token(soporte_user)
        headers = {'Authorization': f'Bearer {token}'}
        
        response = client.post('/api/maintenance-orders', headers=headers, json={
            'orderDate': '2026-05-20',
            'maintenanceType': 'Correctivo',
            'description': 'Repair test',
            'responsible': 'Support Team'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['maintenanceType'] == 'Correctivo'


class TestAuthorizationErrors:
    """Test authorization errors across endpoints."""
    
    def test_cistern_post_non_admin(self, app, client):
        """Test that non-admin cannot create cistern."""
        from app.models import User
        from app.routes.auth import create_token
        
        with app.app_context():
            emp = User(
                first_name="E", last_name="E", address="E",
                dpi="6666666666666", role="empleado"
            )
            emp.set_password("Test123*")
            db.session.add(emp)
            db.session.commit()
            token = create_token(emp)
        
        headers = {'Authorization': f'Bearer {token}'}
        response = client.post('/api/cistern', headers=headers, json={
            'capacityLiters': 20000,
            'currentLiters': 12000
        })
        assert response.status_code == 403
    
    def test_dashboard_non_authorized(self, app, client):
        """Test that users with invalid roles cannot access dashboard."""
        from app.models import User
        from app.routes.auth import create_token
        
        with app.app_context():
            user = User(
                first_name="U", last_name="U", address="U",
                dpi="7777777777777", role="guest"
            )
            user.set_password("Test123*")
            db.session.add(user)
            db.session.commit()
            token = create_token(user)
        
        headers = {'Authorization': f'Bearer {token}'}
        response = client.get('/api/dashboard', headers=headers)
        assert response.status_code == 403
