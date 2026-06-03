import pytest
from app.extensions import db
from app.models import User


class TestAuthRegister:
    """Test authentication register endpoint."""
    
    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post('/api/auth/register', json={
            'firstName': 'New',
            'lastName': 'User',
            'address': '123 Test St',
            'dpi': '9999999999999',
            'password': 'SecurePass123*',
            'confirmPassword': 'SecurePass123*'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Usuario registrado correctamente'
        assert data['user']['dpi'] == '9999999999999'
        assert data['user']['role'] == 'cliente'

    def test_register_ignores_requested_role(self, client):
        """Test public registration always creates cliente users."""
        response = client.post('/api/auth/register', json={
            'firstName': 'New',
            'lastName': 'Admin',
            'address': '123 Test St',
            'dpi': '9999999999998',
            'role': 'administrador',
            'password': 'SecurePass123*',
            'confirmPassword': 'SecurePass123*'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['user']['role'] == 'cliente'
    
    def test_register_missing_fields(self, client):
        """Test registration with missing fields."""
        response = client.post('/api/auth/register', json={
            'firstName': 'New',
            'lastName': 'User'
        })
        assert response.status_code == 400
        assert 'obligatorios' in response.get_json()['error']
    
    def test_register_password_mismatch(self, client):
        """Test registration with mismatched passwords."""
        response = client.post('/api/auth/register', json={
            'firstName': 'New',
            'lastName': 'User',
            'address': '123 Test St',
            'dpi': '8888888888888',
            'password': 'SecurePass123*',
            'confirmPassword': 'DifferentPass123*'
        })
        assert response.status_code == 400
        assert 'no coinciden' in response.get_json()['error']
    
    def test_register_short_password(self, client):
        """Test registration with short password."""
        response = client.post('/api/auth/register', json={
            'firstName': 'New',
            'lastName': 'User',
            'address': '123 Test St',
            'dpi': '7777777777777',
            'password': 'Short1*',
            'confirmPassword': 'Short1*'
        })
        assert response.status_code == 400
        assert '8 caracteres' in response.get_json()['error']
    
    def test_register_duplicate_dpi(self, client, auth_user):
        """Test registration with duplicate DPI."""
        response = client.post('/api/auth/register', json={
            'firstName': 'Another',
            'lastName': 'User',
            'address': '456 Test St',
            'dpi': '1111111111111',
            'password': 'SecurePass123*',
            'confirmPassword': 'SecurePass123*'
        })
        assert response.status_code == 409
        assert 'registrado' in response.get_json()['error']


class TestAuthLogin:
    """Test authentication login endpoint."""
    
    def test_login_success(self, client, auth_user):
        """Test successful login."""
        response = client.post('/api/auth/login', json={
            'dpi': '1111111111111',
            'password': 'Test123*'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'token' in data
        assert data['user']['dpi'] == '1111111111111'
    
    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        response = client.post('/api/auth/login', json={
            'dpi': '1111111111111'
        })
        assert response.status_code == 400
        assert 'obligatorios' in response.get_json()['error']
    
    def test_login_user_not_found(self, client):
        """Test login with non-existent user."""
        response = client.post('/api/auth/login', json={
            'dpi': '0000000000000',
            'password': 'AnyPassword123*'
        })
        assert response.status_code == 404
        assert 'registrado' in response.get_json()['error']
    
    def test_login_wrong_password(self, client, auth_user):
        """Test login with wrong password."""
        response = client.post('/api/auth/login', json={
            'dpi': '1111111111111',
            'password': 'WrongPassword'
        })
        assert response.status_code == 401
        assert 'Credenciales incorrectas' in response.get_json()['error']
    
    def test_login_blocked_account(self, app, client):
        """Test login with blocked account."""
        with app.app_context():
            # Create user directly in the test
            user = User(
                first_name="Admin",
                last_name="Test",
                address="Test Address",
                dpi="1111111111111",
                role="administrador"
            )
            user.set_password("Test123*")
            user.is_blocked = True
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/api/auth/login', json={
            'dpi': '1111111111111',
            'password': 'Test123*'
        })
        assert response.status_code == 423
        assert 'bloqueada' in response.get_json()['error']
    
    def test_login_increments_failed_attempts(self, app, client, auth_user):
        """Test that failed login increments failed attempts."""
        # First attempt
        client.post('/api/auth/login', json={
            'dpi': '1111111111111',
            'password': 'WrongPassword'
        })
        
        with app.app_context():
            user = User.query.filter_by(dpi='1111111111111').first()
            assert user.failed_attempts >= 1


class TestAuthMe:
    """Test authentication me endpoint."""
    
    def test_me_authenticated(self, client, auth_headers):
        """Test getting current user info when authenticated."""
        response = client.get('/api/auth/me', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['firstName'] == 'Admin'
        assert data['role'] == 'administrador'
    
    def test_me_not_authenticated(self, client):
        """Test getting current user info without authentication."""
        response = client.get('/api/auth/me')
        assert response.status_code == 401
    
    def test_me_invalid_token(self, client):
        """Test with invalid token."""
        response = client.get('/api/auth/me', headers={
            'Authorization': 'Bearer invalid_token_here'
        })
        assert response.status_code == 401


class TestTokenCreation:
    """Test JWT token creation."""
    
    def test_token_contains_user_data(self, client, auth_user):
        """Test that token contains proper user data."""
        import jwt
        from app import create_app
        
        app = create_app()
        response = client.post('/api/auth/login', json={
            'dpi': '1111111111111',
            'password': 'Test123*'
        })
        token = response.get_json()['token']
        
        with app.app_context():
            payload = jwt.decode(
                token,
                app.config['JWT_SECRET'],
                algorithms=['HS256']
            )
            assert payload['dpi'] == '1111111111111'
            assert payload['role'] == 'administrador'
            assert 'exp' in payload
