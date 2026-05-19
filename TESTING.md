# Testing Guide

## Descripción

Este proyecto incluye un suite completo de tests unitarios e integración con:
- **Coverage > 80%** de los módulos principales
- **Mocks** para la base de datos (SQLite en memoria)
- **Fixtures** reutilizables para tests
- **Reportes HTML** detallados

## Requisitos Previos

1. Python 3.8+
2. Instalar dependencias de desarrollo

## Instalación

### 1. Instalar dependencias de tests

```bash
pip install -r requirements-test.txt
```

### 2. Instalar la aplicación principal

```bash
pip install -r requirements.txt
```

## Ejecutar Tests

### Ejecución Básica

Ejecutar todos los tests:
```bash
pytest
```

### Ejecución con Verbose

```bash
pytest -v
```

### Ejecutar un archivo específico de tests

```bash
# Solo tests de modelos
pytest tests/test_models.py -v

# Solo tests de autenticación
pytest tests/test_auth.py -v

# Solo tests de API
pytest tests/test_api.py -v
```

### Ejecutar tests de una clase específica

```bash
pytest tests/test_auth.py::TestAuthRegister -v
```

### Ejecutar un test específico

```bash
pytest tests/test_auth.py::TestAuthRegister::test_register_success -v
```

## Generar Reporte de Coverage

### 1. Con reporte en terminal

```bash
pytest --cov=app --cov-report=term
```

### 2. Con reporte HTML (Recomendado)

```bash
pytest --cov=app --cov-report=html --cov-report=term
```

Esto generará un reporte HTML en la carpeta `htmlcov/`. Para visualizarlo:

#### Windows (PowerShell):
```powershell
Start-Process htmlcov/index.html
```

#### Windows (CMD):
```cmd
start htmlcov\index.html
```

#### Linux/Mac:
```bash
open htmlcov/index.html
```

### 3. Con métricas detalladas

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

Esta opción muestra qué líneas NO fueron cubiertas.

## Configuración de Tests

El archivo `pytest.ini` contiene la configuración:

```ini
[pytest]
testpaths = tests                          # Carpeta de tests
python_files = test_*.py                   # Archivos a ejecutar
python_classes = Test*                     # Clases de tests
python_functions = test_*                  # Funciones de tests
addopts = --cov=app --cov-report=html      # Opciones por defecto
```

## Estructura de Tests

### `conftest.py`
Contiene fixtures compartidas por todos los tests:
- `app`: Aplicación Flask con BD en memoria
- `client`: Cliente de prueba HTTP
- `auth_user`: Usuario administrador para pruebas
- `auth_token`: Token JWT válido
- `auth_headers`: Headers con autorización
- Otras fixtures: `house`, `cistern`, `resident`, etc.

### `test_models.py`
Tests para los modelos ORM:
- `TestUserModel`: Tests de usuarios y contraseñas
- `TestHouseModel`: Tests de viviendas
- `TestResidentModel`: Tests de residentes
- `TestCisternModel`: Tests de cisternas
- etc.

### `test_auth.py`
Tests para autenticación:
- `TestAuthRegister`: Tests de registro
- `TestAuthLogin`: Tests de login
- `TestAuthMe`: Tests de obtener usuario actual
- `TestTokenCreation`: Tests de JWT

### `test_api.py`
Tests para endpoints API:
- `TestHealthEndpoint`: Tests de health check
- `TestDashboard`: Tests del dashboard
- `TestCisternEndpoints`: Tests de cisternas
- `TestHousesEndpoints`: Tests de viviendas
- `TestPaymentEndpoints`: Tests de pagos
- `TestAuthorizationErrors`: Tests de autorización

## Mock de Base de Datos

La BD se simula en memoria usando SQLite:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
```

Esto asegura que:
- Los tests sean rápidos
- No dependan de una BD externa
- Cada test tenga una BD limpia y aislada
- No haya efectos secundarios entre tests

## Cobertura Esperada

- **app/models.py**: ~95%
- **app/routes/auth.py**: ~90%
- **app/routes/api.py**: ~85%
- **Overall**: > 80%

## Ejemplos de Ejecución

### Ejemplo 1: Ejecutar con reporte HTML

```bash
pytest --cov=app --cov-report=html --cov-report=term -v
```

Esto:
1. Ejecuta todos los tests en modo verbose
2. Calcula coverage
3. Genera reporte HTML en `htmlcov/index.html`
4. Muestra resumen en terminal

### Ejemplo 2: Ejecutar solo tests que fallan

```bash
pytest --lf
```

### Ejemplo 3: Ejecutar solo tests de autenticación

```bash
pytest tests/test_auth.py --cov=app.routes.auth --cov-report=html -v
```

## Troubleshooting

### Error: "No module named 'app'"

Solución: Ejecutar desde la raíz del proyecto:
```bash
cd /path/to/proyecto-analisis-de-sistemas
pytest
```

### Error: "database is locked"

Esto no debería ocurrir con SQLite en memoria, pero si ocurre:
```bash
pytest --tb=short -v
```

### Ver qué líneas NO tienen cobertura

```bash
pytest --cov=app --cov-report=term-missing
```

Busca el porcentaje y las líneas sin cobertura.

## Integración Continua

Para usar en CI/CD (GitHub Actions, GitLab CI, etc.):

```bash
pytest --cov=app --cov-report=xml --cov-report=html --junitxml=test-results.xml
```

Esto genera:
- `coverage.xml`: Para reportes en el CI
- `htmlcov/`: Reporte visual
- `test-results.xml`: Resultados de tests

## Resultados Esperados

Al ejecutar `pytest`, deberías ver:

```
====== test session starts ======
platform win32 -- Python 3.x.x
collected 87 items

tests/test_models.py ............................ [ 32%]
tests/test_auth.py ............................ [ 65%]
tests/test_api.py ............................ [100%]

====== 87 passed in 2.34s ======
Coverage: 82%
```

¡Éxito! ✅
